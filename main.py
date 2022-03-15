"""
Script to download studies from a DICOMweb server, given their Study Instance UIDs. 

The script loops through the studies, their series and their instances, downloads
one instance at a time as a DICOM part 10 file (i.e. *.dcm file). If a file exists
then it will skip over it. Thus it has basic support for resuming where it left off
in the last time it executed.

Utilizes DICOMwebClient, but supports fallback for some edge cases when DICOMwebClient fails.
"""
import os, time, requests
from dicomweb_client.api import DICOMwebClient

studyUids = ["1.2.3.1","1.2.3.2","1.2.3.3","1.2.3.4"]
rootUrl = "https://example.org/dicomweb"
downloadDir = "/path/to/download-folder/"
sleepInterval = 0 # In seconds, allows "throttling" of retrieval requests to minimize chances of rejected requests

if __name__ == '__main__':
    counterStudy = 0
    counterSeries = 0
    counterInstance = 0
    client = DICOMwebClient(url=rootUrl, qido_url_prefix="", wado_url_prefix="", stow_url_prefix="")
    for studyUid in studyUids:
        counterStudy += 1
        print(f"Processing study {counterStudy} of " + str(len(studyUids)))
        studies = None
        try:
            studies = client.search_for_studies(search_filters={'0020000D': studyUid})
            if( studies is None or len(studies) < 1):
                print("No results found for studyUid: " + studyUid)
                continue
        except Exception as e:
            print(f"Caught exception with studyUid {studyUid}")
            print(e)
            continue
        study = studies[0]

        # Make a download directory for this study
        studyDir = downloadDir + studyUid + '/'
        if( not os.path.exists(studyDir) ):
            os.mkdir(studyDir)

        # Loop through the series and download each separately
        seriesList = client.search_for_series(studyUid)
        for series in seriesList:
            counterSeries += 1
            seriesUid = series['0020000E']['Value'][0]
            seriesDir = studyDir + seriesUid + '/'
            if (not os.path.exists(seriesDir)):
                os.mkdir(seriesDir)
            instances = client.search_for_instances(study_instance_uid=studyUid, series_instance_uid=seriesUid)
            for instance in instances:
                counterInstance += 1
                instanceUid = instance['00080018']['Value'][0]
                instancePath = seriesDir + instanceUid + '.dcm'

                if (not os.path.exists(instancePath)): # Only download it if it hasn't been downloaded already
                    try:
                        instanceData = client.retrieve_instance(study_instance_uid=studyUid, series_instance_uid=seriesUid, sop_instance_uid = instanceUid)
                        instanceData.save_as(instancePath)
                    except Exception as e:
                        # Sometimes the DICOMweb client craps out for certain instances, not sure why. In that case, we can try the "crude" way
                        try:
                            instanceUrl = f"{rootUrl}/studies/{studyUid}/series/{seriesUid}/instances/{instanceUid}"
                            result = requests.get(instanceUrl, headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'}) # This header seems to address an HTTP 500 error I get frequently with one particular API end
                            if( result.status_code != 200 ):
                                raise Exception(f"GET {instanceUrl} returned {result.status_code}")
                            tmp = open(instancePath + ".tmp1", 'wb')
                            tmp.write(result.content)
                            tmp.close()
                            # Hack alert!! Use Linux trickery to strip the multipart clutter
                            cmd = f"tail -n +4 {instancePath}.tmp1 > {instancePath}.tmp2; head -n -1 {instancePath}.tmp2 > {instancePath}; rm -f {seriesDir}/*.tmp1 {seriesDir}/*.tmp2"
                            os.system(cmd)
                        except Exception as e:
                            print(f"Caught exception with studyUid {studyUid} and instanceUid {instanceUid}")
                            print(e)
                    if sleepInterval > 0:
                        time.sleep(sleepInterval)
            # End for each instance
        # End for each series
        #break
    # End for each study
    print(f"Processed {counterStudy} studies, {counterSeries} series and {counterInstance} instances")
