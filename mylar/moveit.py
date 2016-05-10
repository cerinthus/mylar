import mylar
from mylar import db, logger, helpers, updater
import os
import shutil


def movefiles(comicid, comlocation, imported):
    #comlocation is destination
    #comicid is used for rename
    files_moved = []

    myDB = db.DBConnection()

    logger.fdebug('comlocation is : ' + str(comlocation))
    logger.fdebug('original comicname is : ' + str(imported['ComicName']))

    impres = imported['filelisting']
    #impres = myDB.select("SELECT * from importresults WHERE ComicName=?", [ogcname])

    if impres is not None:
        for impr in impres:
            srcimp = impr['comiclocation']
            orig_filename = impr['comicfilename']
            #before moving check to see if Rename to Mylar structure is enabled.
            if mylar.IMP_RENAME and mylar.FILE_FORMAT != '':
                logger.fdebug("Renaming files according to configuration details : " + str(mylar.FILE_FORMAT))
                renameit = helpers.rename_param(comicid, imported['ComicName'], impr['issuenumber'], orig_filename)
                nfilename = renameit['nfilename']
                dstimp = os.path.join(comlocation, nfilename)
            else:
                logger.fdebug("Renaming files not enabled, keeping original filename(s)")
                dstimp = os.path.join(comlocation, orig_filename)

            logger.info("moving " + srcimp + " ... to " + dstimp)
            try:
                shutil.move(srcimp, dstimp)
                files_moved.append({'srid':     imported['srid'],
                                    'filename': impr['comicfilename']})
            except (OSError, IOError):
                logger.error("Failed to move files - check directories and manually re-run.")

        logger.fdebug("all files moved.")
        #now that it's moved / renamed ... we remove it from importResults or mark as completed.

    if len(files_moved) > 0:
        for result in files_moved:
            controlValue = {"ComicFilename": result['filename'],
                            "SRID":          result['srid']}
            newValue = {"Status":            "Imported",
                        "ComicID":           comicid}
            myDB.upsert("importresults", newValue, controlValue)
    return

def archivefiles(comicid, ogdir, ogcname):
    myDB = db.DBConnection()
    # if move files isn't enabled, let's set all found comics to Archive status :)
    result = myDB.select("SELECT * FROM importresults WHERE ComicName=?", [ogcname])
    if result is None:
        pass
    else:
        scandir = []
        for res in result:
            if any([os.path.dirname(res['ComicLocation']) in x for x in scandir]):
                pass
            else:
                scandir.append(os.path.dirname(res['ComicLocation']))

        for sdir in scandir:
            logger.info('Updating issue information and setting status to Archived for location: ' + sdir)
            updater.forceRescan(comicid, archive=sdir) #send to rescanner with archive mode turned on

        logger.info('Now scanning in files.')
        updater.forceRescan(comicid)

    return
