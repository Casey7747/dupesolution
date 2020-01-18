# dupesolution
Finds duplicate files and deletes them. CLI

1) Run the program in 'find' mode.
2) Check the files it creates.
3) Modify paths list to exclude paths you dont want to delete from. 
4) Run in dryrun mode to check output.
5) Run in 'delete' mode to delete duplicate files.


usage: find.py [-h] --mode [find/delete/dryrun]
               [--target [target [target ...]]] [--exclude [str [str ...]]]
               [--include [str [str ...]]] [--miniHashSize bytes]
               [--incvms [INCVMS]] [--media [INCMEDIA]]


Check for duplicates and delete them.


optional arguments:
  -h, --help            show this help message and exit
  
  --mode [find/delete/dryrun]
            [find] Find duplicates. [delete] delete duplicates.
            [dryrun] Run delete without actually deleting.
  --target [target [target ...]]
                          destinations(s) to check for duplicates.
  --exclude [str [str ...]]
                        Strings in the filename or path to exlcude from
                        duplicate list. Any in the list will result in
                        exclusion. "OR function". Case insensitive. Exclude
                        overrides Include.
  --include [str [str ...]]
                        Strings which must be present in filename or path to
                        add to duplicate list. Any in the list will result in
                        inclusion. "OR function". Case insensitive. Exclude
                        overrides Include.
  --miniHashSize bytes  Size (in Bytes) to use for Mini Hash check.
  --incvms [INCVMS]     Setting [True] allows deletion of detected Virtual
                        Machine files which may have valid duplicates.
  --media [INCMEDIA]    Setting adds common media file extensions to the
                        include list. Extensions used are: .mp4 .mkv .avi .wma .3gp .flv .m4p .mpeg .mpg .m4v .swf .mov .h264 .h265 .3g2 .rm .vob .mp3 .wav .ogg .3ga .4md .668 .669 .6cm
                        .8cm .abc .amf .ams .wpl .cda .mid .midi .mpa .wma
                        .jpg .jpeg .bmp .mpo .gif .png .tiff .tif .psd .svg
                        .ai .ico .ps .pdf .doc .docx .xls .xlsx .ppt .pptx
                        .txt .pps .ods .xlr .odt .wps .wks .wpd .key .odp .rtf
                        .tex
