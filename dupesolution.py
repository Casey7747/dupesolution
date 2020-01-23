#!/usr/bin/env python3
import sys
import os
import hashlib
import ntpath
import os
import argparse
import atexit
import pickle
import logging
import time
import uuid
start_time = time.time()

video = [".mp4", ".mkv", ".avi", ".wma", ".3gp", ".flv", ".m4p", ".mpeg",
	".mpg", ".m4v", ".swf", ".mov", ".h264", ".h265", ".3g2", ".rm", ".vob"]
audio = [".mp3", ".wav", ".ogg", ".3ga", ".4md", ".668", ".669", ".6cm",
	".8cm", ".abc", ".amf", ".ams", ".wpl", ".cda", ".mid", ".midi", ".mpa", ".wma"]
images = [".jpg", ".jpeg", ".bmp", ".mpo", ".gif", ".png", ".tiff", ".tif",
	".psd", ".svg", ".ai", ".ico", ".ps"]
documents = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt",
	".pps", ".ods", ".xlr", ".odt", ".wps", ".wks", ".wpd", ".key", ".odp",
	".rtf", ".tex"]
executables = [".exe"  ".bat", ".apk", ".bin", ".cgi", ".pl", ".com", ".jar", ".py", ".wsf"]
compressed = [".zip", ".7z", ".ace", ".rar", ".deb", ".pkg", ".rpm", ".tar", ".z"]
other = [".iso", ".csv", ".log", ".dmg", ".vcd"]
vmFileList = [".vmdk",".vmx",".vmsd",".vmxf",".appinfo",".nvram",".vmem",".vmss"]
media = video + audio + images + documents

class pgmVars:
	volume = 0
	hashes_full = {}
	hashes_on_1k = {}
	hashes_by_size = {}
	
	dupeList = list()
	vmPathList = list()
	delListPath = list()
	delList = list()
	delPaths = list()

class duplicateItem:
	def __init__(self):
		self.hash = 0
		self.filename = list()
		self.dupeNo = -1
		self.path = list()
		self.name = list()
		self.dupeCount = 0
		self.location = 0

def goodbye():
	parser.print_help(sys.stderr)
	sys.exit(0)

def getName(filename):
	return os.path.basename(filename)

def getPath(filename):
	return os.path.split(filename)[0]

def chunk_reader(fobj, chunk_size=1024):
	"""Generator that reads a file in chunks of bytes"""
	while True:
		chunk = fobj.read(chunk_size)
		if not chunk:
			return
		yield chunk

def get_hash(filename, first_chunk_only=False, hash=hashlib.sha1):
	hashobj = hash()
	file_object = open(filename, 'rb')

	if first_chunk_only:
		size = int(args.miniSize[0])
		hashobj.update(file_object.read(size))
	else:
		for chunk in chunk_reader(file_object):
			hashobj.update(chunk)
	hashed = hashobj.digest()
	file_object.close()
	return hashed

def checkHashExists(full_hash):
	i = 0
	for dupe in pgmVars.dupeList:
		if full_hash == dupe.hash:
			return i
		i = i + 1
	return None

def check_not_in_exclude(dirpath, filename):
	full_path = os.path.join(dirpath, filename).lower()
	directory = dirpath.lower()
	fname = filename.lower()
	if(args.exclude):
		for excludeString in args.exclude:
			if not (full_path.find(excludeString.lower()) == -1):
				#logging.info ("Excluding due to \"", excludeString, "\" being found in ", full_path)
				logging.info ("Excluding due to \"'%s'\" being found in '%s'"% (excludeString,full_path))
				return False
	for excludePath in pgmVars.vmPathList:
		if not (directory.find(excludePath.lower()) == -1):
			#logging.info ("Excluding due to \"", excludePath, "\" path found in ", full_path)
			logging.info ("Excluding due to \"'%s'\" being found in '%s'"% (excludePath,full_path))
			return False
	if(args.incVMs):
		for excludeString in vmFileList:
			if not (full_path.find(excludeString.lower()) == -1):
				#logging.info ("Excluding due to \"", excludeString, "\" being found in ", full_path)
				logging.info ("Excluding due to \"'%s'\" being found in '%s'"% (excludeString,full_path))
				pgmVars.vmPathList.append(dirpath)
				return False
	return True
	
def check_in_include(dirpath, filename):
	full_path = os.path.join(dirpath, filename).lower()
	if(args.include):
		for includeString in args.include:
			if not (full_path.find(includeString.lower()) == -1):
				return True
	elif (args.incMedia):
		for includeString in media:
			if not (filename.find(includeString.lower()) == -1):
					return True
	else:
		return True
	return False

def check_for_duplicate_size(paths, hash=hashlib.sha1):
	fileCount = 0
	print("=========================================================================")
	print ("Checking for duplicate file sizes", paths)
	for path in paths:
		for dirpath, dirnames, filenames in os.walk(path):
			for filename in filenames:
				full_path = os.path.join(dirpath, filename)
				#If not in exclude lists process.
				if (check_not_in_exclude(dirpath, filename) & check_in_include(dirpath, filename)):
					#Get path and size
					try:
						# if the target is a symlink (soft one), this will 
						# dereference it - change the value to the actual target file
						full_path = os.path.realpath(full_path)
						file_size = os.path.getsize(full_path)
					except (OSError,):
						# not accessible (permissions, etc) - pass on
						continue
					#Return index of matched if duplicate exists
					duplicate = pgmVars.hashes_by_size.get(file_size)

					if duplicate:
						pgmVars.hashes_by_size[file_size].append(full_path)
					else:
						pgmVars.hashes_by_size[file_size] = []	# create the list for this file size
						pgmVars.hashes_by_size[file_size].append(full_path)
					fileCount += 1
	print("Searched",fileCount ,"files.")
	print("Found",len(pgmVars.hashes_by_size),"different file sizes.")
	print("=========================================================================")
	
def check_for_duplicate_mini(paths, hash=hashlib.sha1):
	searchedMiniHashCount = 0
	prog = 0
	progTotal = len(pgmVars.hashes_by_size.items())
	# For all files with the same file size, get their hash on the 1st 1024 bytes
	print ("Checking for duplicate mini hash")
	#printProgressBar(0, progTotal, prefix = 'Progress:', suffix = 'Complete', length = 50)
	for __, files in pgmVars.hashes_by_size.items():
		prog += 1
		if len(files) < 2:
			continue	# this file size is unique, no need to spend cpy cycles on it
		for filename in files:
			try:
				small_hash = get_hash(filename, first_chunk_only=True)
			except (OSError,):
				# the file access might've changed till the exec point got here 
				logging.warn ("Couldn't open file: '%s'"% (filename))
				c1 = c1 + 1
				continue
			duplicate = pgmVars.hashes_on_1k.get(small_hash)
			if duplicate:
				pgmVars.hashes_on_1k[small_hash].append(filename)
			else:
				pgmVars.hashes_on_1k[small_hash] = []		  # create the list for this 1k hash
				pgmVars.hashes_on_1k[small_hash].append(filename)
			searchedMiniHashCount += 1
			printProgressBar(prog, progTotal, prefix = 'Progress:', suffix = 'Complete', length = 50)	
	print("Searched",searchedMiniHashCount, "files.")
	print("Found",len(pgmVars.hashes_on_1k) ,"unique files with possible duplicates.")
	print("=========================================================================")

def check_for_duplicate_full(paths, hash=hashlib.sha1):
	searchedHashCount = 0
	duplicateFileCount = 0
	dupeHashCount = 0 #Estimated amount to be deleted	
	prog = 0
	progTotal = len(pgmVars.hashes_on_1k.items())
	# For all files with the hash on the 1st 1024 bytes, get their hash on the full file - collisions will be duplicates
	print ("Checking for duplicate full hash")
	printProgressBar(prog, progTotal, prefix = 'Progress:', suffix = 'Complete', length = 50)
	for __, files in pgmVars.hashes_on_1k.items():
		prog += 1
		if len(files) < 2:
			continue	# this hash of fist 1k file bytes is unique, no need to spend cpy cycles on it
		for filename in files:
			try:
				full_hash = get_hash(filename, first_chunk_only=False)
			except (OSError,):
				# the file access might've changed till the exec point got here 
				logging.warn ("Couldn't open file: '%s'"% (filename))
				continue
			duplicate = pgmVars.hashes_full.get(full_hash)
			if duplicate:
				duplicateFileCount += 1
				dupeHashCount += 1
				exists = checkHashExists(full_hash)
				if (exists != None) :	#Add to existing duplicate list
					pgmVars.dupeList[exists].filename.append(filename)				
					pgmVars.dupeList[exists].name.append(getName(filename))
					pgmVars.dupeList[exists].path.append(getPath(filename))
					pgmVars.dupeList[exists].dupeCount += 1
				else:	#New Duplicate Entry
					newDupe = duplicateItem()
					newDupe.hash = full_hash

					newDupe.filename.append(filename)
					newDupe.name.append(getName(filename))
					newDupe.path.append(getPath(filename))

					newDupe.filename.append(duplicate)
					newDupe.name.append(getName(duplicate))
					newDupe.path.append(getPath(duplicate))
					newDupe.dupeCount = 2
					pgmVars.dupeList.append(newDupe)
					dupeHashCount += 1
			else:
				pgmVars.hashes_full[full_hash] = filename
			searchedHashCount += 1
		printProgressBar(prog, progTotal, prefix = 'Progress:', suffix = 'Complete', length = 50)
	print("Searched",searchedHashCount, "files.")
	print("Found",dupeHashCount ,"duplicate files(total).")
	print("Found",duplicateFileCount ,"duplicates viable for deletion.")
	print("=========================================================================")
	
def check_for_duplicates(paths, hash=hashlib.sha1):
	check_for_duplicate_size(paths, hash)
	check_for_duplicate_mini(paths, hash)
	check_for_duplicate_full(paths, hash)

def getDupePaths():
	pathList = list()
	for dupe in pgmVars.dupeList:
		for path in dupe.path:
			pathList.append(path)
	return sorted(list(set(pathList)), key=len, reverse=True)

def addToDeletion():
	print ("Unique Files: ", len(pgmVars.dupeList))
	for dupe in pgmVars.dupeList:	#Loop through each set of duplicates
		tryCount = 0	#Overall attempt count
		delIndex = 0	#Index of paths to check through
		maxCheckLen = len(pgmVars.delListPath)*len(dupe.filename)
		check = True
		while (len(dupe.filename) > 1 and check ):	#Loop until only one item left or break.
			try:
				index = dupe.path.index(pgmVars.delListPath[delIndex])	#If path is (ith) delete path return index.
			except:
				delIndex += 1
				if delIndex > len(pgmVars.delListPath):
					check = False
				continue
			else:
				logging.info ("Adding to delete list '%s%s'"% (dupe.path[index],dupe.filename[index] ))
				#Add file and path to delete list
				pgmVars.delList.append(dupe.filename[index])
				pgmVars.delPaths.append(dupe.path[index])
				#Find & remove from current dupe set
				dupe.filename.remove(dupe.filename[index])
				dupe.name.remove(dupe.name[index])
				dupe.path.remove(dupe.path[index])
				
			tryCount += 1
			if(tryCount > maxCheckLen):
				raise ValueError('addToDeletion: tryCount exceeded macCheckLen. This should not happen.')
				check = False

def pathsToFile():
	with open('duplicate_files_path_list.txt', 'w') as filehandle:
		for listitem in getDupePaths():
			filehandle.write('%s\n' % listitem)

def pathsFromFile():
	with open('duplicate_files_path_list.txt', 'r') as filehandle:
		for line in filehandle:
			currentPlace = line[:-1]
			pgmVars.delListPath.append(currentPlace)

def filesToFile():
	with open('duplicate_file_list.txt', 'w') as filehandle:
		for dupe in pgmVars.dupeList:
			filehandle.write('%s\n' % dupe.filename)

def deleteToFile():
	with open('delete_file_list.txt', 'w') as filehandle:
		for fname in pgmVars.delList:
			filehandle.write('%s\n' % fname)
			
def hashedListToFile():
	with open('hashed_list.dat', 'wb') as filehandle:
		pickle.dump(pgmVars.dupeList, filehandle)
		filehandle.close()

def hashedListFromFile():
	with open('hashed_list.dat', 'rb') as filehandle:
		newList = pickle.load(filehandle)
		filehandle.close()
	return newList
	
def bySizeToFile():
	logging.info ("Storing sizes in file: '%s'"% pgmVars.hashes_by_size)
	try:
		with open('hashes_by_size.dat', 'wb') as filehandle:
			pickle.dump(pgmVars.hashes_by_size, filehandle)
			filehandle.close()
	except (OSError, IOError) as e:
		logging.error("File write failed: pgmVars.hashes_by_size.dat")

def bySizeFromFile():
	try:
		with open('hashes_by_size.dat', 'rb') as filehandle:
			pgmVars.hashes_by_size = pickle.load(filehandle)
			filehandle.close()
	except (OSError, IOError) as e:
		pass
	logging.info ("Readings sizes from file: '%s'"% pgmVars.hashes_by_size)
	
def by1kToFile():
	try:
		with open('hashes_on_1k.dat', 'wb') as filehandle:
			pickle.dump(pgmVars.hashes_on_1k, filehandle)
			filehandle.close()
	except (OSError, IOError) as e:
		logging.error("File write failed: pgmVars.hashes_on_1k.dat")
		
def by1kFromFile():
	try:
		with open('hashes_on_1k.dat', 'rb') as filehandle:
			pgmVars.hashes_on_1k = pickle.load(filehandle)
			filehandle.close()
	except (OSError, IOError) as e:
		pass

def byHashToFile():
	try:
		with open('hashes_full.dat', 'wb') as filehandle:
			pickle.dump(pgmVars.hashes_full, filehandle)
			filehandle.close()
	except (OSError, IOError) as e:
		logging.error("File write failed: pgmVars.hashes_full.dat")
		
def byHashFromFile():
	try:
		with open('hashes_full.dat', 'rb') as filehandle:
			pgmVars.hashes_full = pickle.load(filehandle)
			filehandle.close()
	except (OSError, IOError) as e:
		pass
		
def deleteItems():
	logging.info ("Number of items for deletion: %s"% len(pgmVars.delList))
	for item in pgmVars.delList:
		os.remove(item)
		pass

def checkArgs(targets):
	#Check for duplicates
	for target in targets:
		if (targets.count(target) > 1):
			logging.error("ERROR: duplicate paths not allowed.")
			goodbye()
	#Check for substring - Forward
	targetList = targets.copy()
	while(len(targetList) > 0):
		test = targetList.pop()
		if any(test in s for s in targetList):
			logging.error("ERROR: Target folder list must not contain their own children.")
			goodbye()
	#Check for substring - Backward
	targetList = targets.copy()
	while(len(targetList) > 0):
		test = targetList.pop(0)
		if any(test in s for s in targetList):
			logging.error("ERROR: Target folder list must not contain their own children.")
			goodbye()

def staged_find(stage, paths):
	if (stage == 1):
		bySizeFromFile()
		check_for_duplicate_size(paths, hash)
		bySizeToFile()
	elif (stage == 2):
		bySizeFromFile()
		by1kFromFile()
		check_for_duplicate_mini(paths, hash)
		by1kToFile()
	elif (stage == 3):
		by1kFromFile()
		byHashFromFile()
		check_for_duplicate_full(paths, hash)	
		byHashToFile()
		hashedListToFile()
		pathsToFile()
		filesToFile()
	
""" Thanks to https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console for this snippet"""		
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

# Argument parser and program initiliisiiaizion
parser = argparse.ArgumentParser(description='Check for duplicates and delete them.')
parser.add_argument('--mode', metavar='[find/delete/dryrun]', type=str, dest='mode', nargs=1, default='find', required=True,
					help='[find] Find duplicates.\n [delete] delete duplicates.\n [dryrun] Run delete without actually deleting.')
parser.add_argument('--target', metavar='target',dest='target', type=str, nargs='*', required=False,
					help='destinations(s) to check for duplicates.')
parser.add_argument('--exclude', metavar='str',dest='exclude', type=str, nargs='*', required=False,
					help="""Strings in the filename or path to exlcude from duplicate list.
					Any in the list will result in exclusion. \"OR function\".
					Case insensitive. Exclude overrides Include.""")
parser.add_argument('--include', metavar='str',dest='include', type=str, nargs='*', required=False,
					help="""Strings which must be present in filename or path to add to duplicate list.
					Any in the list will result in inclusion. \"OR function\".
					Case insensitive. Exclude overrides Include.""")
parser.add_argument('--miniHashSize', metavar='bytes',dest='miniSize', type=int, nargs=1, required=False, default=[1024],
					help='Size (in Bytes) to use for Mini Hash check.')
parser.add_argument('--incvms', dest='incVMs', default=True, const=False, nargs='?',
					required=False, help='Setting [True] allows deletion of detected Virtual Machine files which may have valid duplicates.')
parser.add_argument('--stage', dest='stage',  nargs=1, type=int,
					required=False, help="""Staged collection. For use where all systems are not available to the one processor.
					1 = Collect file sizes. 2 = Collect mini hash. 3 = Collect full hash. Must be used with find mode.""")
parser.add_argument('--media', dest='incMedia', default=False, const=True, nargs='?',
					required=False, help="""Setting adds common media file extensions to the include list.
					Extensions used are: .mp4 .mkv .avi .wma .3gp .flv .m4p .mpeg .mpg .m4v .swf .mov .h264 .h265 .3g2 .rm .vob .mp3 .wav .ogg
					.3ga .4md .668 .669 .6cm .8cm .abc .amf .ams .wpl .cda .mid .midi .mpa .wma .jpg .jpeg .bmp .mpo .gif .png .tiff .tif .psd
					.svg .ai .ico .ps .pdf .doc .docx .xls .xlsx .ppt .pptx .txt .pps .ods .xlr .odt .wps .wks .wpd .key .odp .rtf .tex""")
print("UUID:")
print (uuid.UUID(int=uuid.getnode()))
args = parser.parse_args()
logging.basicConfig(filename='find.log',level=logging.DEBUG)

if (args.stage):
	if((args.mode[0].lower() == "find") & (args.stage[0] > 0 & args.stage[0] <5)):
		print ("Staged Find '%s'"% args.stage)
		checkArgs(args.target)
		staged_find(args.stage[0], args.target)
	else:
		goodbye()

elif (args.mode[0].lower() == "find"):
	targetList = args.target
	print ("Find Mode")
	checkArgs(targetList)
	check_for_duplicates(args.target)
	hashedListToFile()
	pathsToFile()
	filesToFile()
elif (args.mode[0].lower() == "delete"):
	print ("Delete Mode")
	pgmVars.dupeList = hashedListFromFile()
	pathsFromFile()
	addToDeletion()
	deleteToFile()
	deleteItems()
elif (args.mode[0].lower() == "dryrun"):
	print ("Dry Run")
	pgmVars.dupeList = hashedListFromFile()
	pathsFromFile()
	addToDeletion()
	deleteToFile()
else:
	goodbye()
print("%.3f seconds" % (time.time() - start_time))
