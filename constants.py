ARCHIVE_EXTENSIONS = [
	'.zip',
	'.rar',
	'.7z',
	'.tar',
	'.gz',
	'.bz2',
	'.tgz'
]

TEMP_EXTENSIONS = [
	'.crdownload',
	'.part',
	'.download',
	'.inprogress',
	'._mp', '.partial',
	'.dms', '.bak',
	'.opdownload',
	'.!ut', '.bc!', '.xltd',
	'.filepart',
	'.tmp', '.unfinished', '.aria2'
]

# Directory where archives will be safely extracted for analysis
UNPACK_ROOT_DIR = 'unpacked_analysis_queue'

# Maximum number of files to extract from a single archive (to prevent zip bombs)
MAX_FILES_TO_EXTRACT = 100
