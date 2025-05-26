from data.models import *

class RequestAndFeedbackAPIController:
    def __init__(self, db):
        self.db : SQLAlchemy = db

    def processNewFeatureRequest(self, featureDescription, featureUseCase, featureExpected, featureDetails, submitter_name=None):
        featureRequest = NewFeatureRequest(
            description=featureDescription,
            use_case=featureUseCase,
            expected=featureExpected,
            details=featureDetails,
            submitter_name=submitter_name
        )
        
        self.db.session.add(featureRequest)
        self.db.session.commit()

        self.db.session.commit()
        return featureRequest.id

    def processBugReport(self, bugDescription, whenItOccurs, expectedBehavior, stepsToReproduce, submitter_name=None):
        bugReport = BugReport(
            description=bugDescription,
            when_occurs=whenItOccurs,
            expected_behavior=expectedBehavior,
            steps_to_reproduce=stepsToReproduce,
            submitter_name=submitter_name
        )
        
        self.db.session.add(bugReport)
        self.db.session.commit()

        self.db.session.commit()
        return bugReport.id

    def processSongRequest(self, songName, naughtyWords, submitter_name=None):
        songRequest = SongRequest(
            song_name=songName,
            naughty_words= naughtyWords,
            submitter_name=submitter_name
        )
        
        self.db.session.add(songRequest)
        self.db.session.commit()

        self.db.session.commit()
        return songRequest.id
    
    def getFeatureRequests(self):
        featureRequests = self.db.session.query(NewFeatureRequest).all()
        return featureRequests
    
    def getBugReports(self):
        bugReports = self.db.session.query(BugReport).all()
        return bugReports
    
    def getSongRequests(self):
        songRequests = self.db.session.query(SongRequest).all()
        return songRequests