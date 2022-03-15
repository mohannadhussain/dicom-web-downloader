# DICOMweb Downloader
Script to download studies from a DICOMweb server, given their Study Instance UIDs. 

The script loops through the studies, their series and their instances, downloads
one instance at a time as a DICOM part 10 file (i.e. *.dcm file). If a file exists
then it will skip over it. Thus it has basic support for resuming where it left off
in the last time it executed.

Utilizes DICOMwebClient, but supports fallback for some edge cases when DICOMwebClient fails.

# Usage
## 1) Fill in the blanks
Update the following variables:
* `studyUids` An array/list of Study Instance UIDs you want to download
* `rootUrl` The URL to the root of the DICOMweb service you're about to download from
* `downloadDir` Local directory to write the DICOM files to. The script will write each file as subfolders like so: `<study UID>/<series UID>/instanceUID.dcm`
* (Optional) `sleepInterval` If you need to throttle retrieval requests to minimize chances of rejected requests. In seconds.

## 2) Install dependencies
`pip3 install DICOMwebClient`

## 3) Run
`python3 main.py`
