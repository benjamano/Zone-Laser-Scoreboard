from data.models import *

class RequestProcessor:
    def __init__(self, db):
        self.db = db

    def processNewFeatureRequest(self, featureDescription, featureUseCase, featureExpected, featureDetails, submitter_name=None):
        featureRequest = NewFeatureRequest(
            description=featureDescription,
            use_case=featureUseCase,
            expected=featureExpected,
            details=featureDetails,
            request_id="FR-0",
            submitter_name=submitter_name
        )
        
        self.db.session.add(featureRequest)
        self.db.session.commit()

        featureRequest.request_id = f"FR-{featureRequest.id}"
        self.db.session.commit()
        return featureRequest.request_id

    def processBugReport(self, bugDescription, whenItOccurs, expectedBehavior, stepsToReproduce, submitter_name=None):
        bugReport = BugReport(
            description=bugDescription,
            when_occurs=whenItOccurs,
            expected_behavior=expectedBehavior,
            steps_to_reproduce=stepsToReproduce,
            request_id="BR-0",
            submitter_name=submitter_name
        )
        
        self.db.session.add(bugReport)
        self.db.session.commit()

        bugReport.request_id = f"BR-{bugReport.id}"
        self.db.session.commit()
        return bugReport.request_id

    def processSongRequest(self, songName, naughtyWords, submitter_name=None):
        songRequest = SongRequest(
            song_name=songName,
            naughty_words=naughtyWords,
            request_id="SR-0", 
            submitter_name=submitter_name
        )
        
        self.db.session.add(songRequest)
        self.db.session.commit()

        songRequest.request_id = f"SR-{songRequest.id}"
        self.db.session.commit()
        return songRequest.request_id