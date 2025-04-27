from webApp import db
from data.models import *

def processNewFeatureRequest(featureDescription, featureUseCase, featureExpected, featureDetails, submitter_name=None):
    featureRequest = NewFeatureRequest(
        description=featureDescription,
        use_case=featureUseCase,
        expected=featureExpected,
        details=featureDetails,
        request_id="FR-0",
        submitter_name=submitter_name
    )
    
    db.session.add(featureRequest)
    db.session.commit()

    featureRequest.request_id = f"FR-{featureRequest.id}"
    db.session.commit()
    return featureRequest.request_id

def processBugReport(bugDescription, whenItOccurs, expectedBehavior, stepsToReproduce, submitter_name=None):
    bugReport = BugReport(
        description=bugDescription,
        when_occurs=whenItOccurs,
        expected_behavior=expectedBehavior,
        steps_to_reproduce=stepsToReproduce,
        request_id="BR-0",
        submitter_name=submitter_name
    )
    
    db.session.add(bugReport)
    db.session.commit()

    bugReport.request_id = f"BR-{bugReport.id}"
    db.session.commit()
    return bugReport.request_id

def processSongRequest(songName, naughtyWords, submitter_name=None):
    songRequest = SongRequest(
        song_name=songName,
        naughty_words=naughtyWords,
        request_id="SR-0", 
        submitter_name=submitter_name
    )
    
    db.session.add(songRequest)
    db.session.commit()

    songRequest.request_id = f"SR-{songRequest.id}"
    db.session.commit()
    return songRequest.request_id
