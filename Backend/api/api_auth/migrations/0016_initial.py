from django.db import migrations

class Migration(migrations.Migration):
    initial = True
    dependencies=[]
    operations=[
        migrations.RunSQL(
            """
                CREATE TABLE Categories (
                    CategoryID SERIAL PRIMARY KEY,
                    CategoryText VARCHAR(100),
                    NumOfCourses INT DEFAULT 0
                );

                CREATE TABLE Instructor (
                    InstructorID BIGSERIAL PRIMARY KEY NOT NULL,
                    InstructorName VARCHAR(100) NOT NULL,
                    Email VARCHAR(127) UNIQUE NOT NULL CHECK (Email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
                    Username VARCHAR(255) UNIQUE NOT NULL,
                    Password VARCHAR(255) NOT NULL,
                    ProfilePic TEXT DEFAULT NULL,
                    BIO TEXT,
                    Rating INT DEFAULT 0 CHECK (Rating >= 0 AND Rating <= 5),
                    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    SocialMediaAccount TEXT[],
                    Balance Decimal(10,2) DEFAULT 0
                );

                CREATE TABLE Student (
                    StudentID BIGSERIAL PRIMARY KEY NOT NULL,
                    StudentName VARCHAR(100) NOT NULL,
                    Email VARCHAR(127) UNIQUE NOT NULL CHECK (Email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
                    Username VARCHAR(255) UNIQUE NOT NULL,
                    Password VARCHAR(255) NOT NULL,
                    ProfilePic TEXT DEFAULT NULL,
                    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    Balance Decimal(10,2) DEFAULT 0
                );

                CREATE TYPE CourseStatus AS ENUM ('public', 'private');

                CREATE TABLE Course (
                    CourseID SERIAL PRIMARY KEY NOT NULL,
                    Title VARCHAR(100) NOT NULL,
                    Description TEXT NOT NULL,
                    TopInstructorID INT REFERENCES Instructor(InstructorID)
                        ON DELETE CASCADE,
                    CategoryID INT REFERENCES Categories(CategoryID) 
                        ON DELETE CASCADE,
                    SeenStatus CourseStatus, --public or private
                    Duration INTERVAL NOT NULL DEFAULT INTERVAL '0',
                    CreatedAt TIMESTAMP Default CURRENT_TIMESTAMP,
                    Price Decimal(8,2) CHECK (Price >= 0) NOT NULL,
                    Rating INT DEFAULT 0 CHECK (Rating >= 0 AND Rating <= 5),
                    Requirements TEXT[],
                    CourseImage TEXT DEFAULT NULL,
                    Certificate TEXT DEFAULT NULL --link of the certificate image
                );

                CREATE TABLE Course_Instructor (
                    CourseID INT,
                    InstructorID INT,
                    PRIMARY KEY (CourseID, InstructorID),
                    FOREIGN KEY (CourseID) REFERENCES Course(CourseID) ON DELETE CASCADE,
                    FOREIGN KEY (InstructorID) REFERENCES Instructor(InstructorID) ON DELETE CASCADE
                );

                CREATE TABLE Student_Course (
                    CourseID INT NOT NULL,
                    StudentID INT NOT NULL,
                    PurchaseDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    StudentProgress DECIMAL(3,1) DEFAULT 0,
                    PRIMARY KEY (CourseID, StudentID),
                    FOREIGN KEY (CourseID) REFERENCES Course(CourseID)
                        ON DELETE CASCADE,
                    FOREIGN KEY (StudentID) REFERENCES Student(StudentID)
                        ON DELETE CASCADE
                );

                CREATE TABLE CourseSection (
                    CourseSectionID SERIAL PRIMARY KEY,
                    CourseID INT REFERENCES Course(CourseID) ON DELETE CASCADE,
                    Title VARCHAR(100) NOT NULL,
                    Duration INTERVAL DEFAULT INTERVAL '0'
                );

                CREATE TABLE Video (
                    VideoID BIGSERIAL PRIMARY KEY,
                    CourseSectionID INT REFERENCES CourseSection(CourseSectionID)
                        ON DELETE CASCADE NOT NULL,
                    VideoLink TEXT NOT NULL,
                    VideoDuration INTERVAL NOT NULL DEFAULT INTERVAL '0',
                    Title VARCHAR(100) NOT NULL
                );

                CREATE TABLE Video_Student (
                    VideoID INT REFERENCES Video(VideoID) ON DELETE CASCADE,
                    StudentID INT REFERENCES Student(StudentID) ON DELETE CASCADE,
                    VideoProgress DECIMAL(4,2) CHECK (VideoProgress >= 0 AND VideoProgress <= 100),
                    CreatedAt TIMESTAMP Default CURRENT_TIMESTAMP,
                    PRIMARY KEY (VideoID, StudentID)
                );

                CREATE TABLE QA (
                    QAID SERIAL PRIMARY KEY,
                    VideoID INT REFERENCES Video(VideoID)
                        ON DELETE CASCADE NOT NULL
                );

                CREATE TABLE Chat (
                    ChatID BIGSERIAL PRIMARY KEY,
                    StudentID INT REFERENCES Student(StudentID) NOT NULL,
                    CourseID INT REFERENCES Course(CourseID) NOT NULL,
                    InstructorID INT REFERENCES Instructor(InstructorID) NOT NULL,
                    UNIQUE (StudentID, CourseID, InstructorID)
                );

                CREATE TABLE Messages (
                    MessageID SERIAL PRIMARY KEY NOT NULL,
                    MessageText TEXT NOT NULL,
                    isAnswer BOOLEAN NOT NULL, -- true -> answer, false -> question
                    AnswerTo INT REFERENCES Student(StudentID) ON DELETE SET NULL,
                    SenderStudentID INT REFERENCES Student(StudentID) ON DELETE SET NULL,
                    SenderInstructorID INT REFERENCES Instructor(InstructorID) ON DELETE SET NULL,
                    QAID INT REFERENCES QA(QAID) ON DELETE CASCADE,
                    ChatID INT REFERENCES Chat(ChatID) ON DELETE CASCADE,
                    CreatedAt TIMESTAMP Default CURRENT_TIMESTAMP,
                    CHECK (
                        (QAID IS NOT NULL AND ChatID IS NULL) OR
                        (QAID IS NULL AND ChatID IS NOT NULL)
                    )
                );

                CREATE TYPE ExamType AS ENUM ('quiz', 'contest');

                CREATE TABLE QuizExam (
                    QuizExamID BIGSERIAL PRIMARY KEY,
                    Title TEXT,
                    SectionID INT REFERENCES CourseSection(CourseSectionID) ON DELETE CASCADE NOT NULL,
                    InstructorID INT REFERENCES Instructor(InstructorID) ON DELETE CASCADE,
                    ExamKind ExamType DEFAULT 'quiz',
                    Duration INTERVAL,
                    TotalMarks DECIMAL(10, 2),
                    PassingMarks DECIMAL(10, 2),
                    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE ContestExam (
                    ContestExamID BIGSERIAL PRIMARY KEY,
                    Title TEXT,
                    CourseID INT REFERENCES Course(CourseID) ON DELETE CASCADE NOT NULL,
                    InstructorID INT REFERENCES Instructor(InstructorID) ON DELETE CASCADE NOT NULL,
                    ExamKind ExamType DEFAULT 'contest',
                    Duration INTERVAL,
                    TotalMarks DECIMAL(10, 2),
                    PassingMarks DECIMAL(10, 2),
                    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE Questions (
                    QuestionID BIGSERIAL PRIMARY KEY,
                    QuizExamID INT REFERENCES QuizExam(QuizExamID) ON DELETE CASCADE,
                    ContestExamID INT REFERENCES ContestExam(ContestExamID) ON DELETE CASCADE,
                    QuestionText TEXT NOT NULL,
                    Choices TEXT[],
                    CorrectAnswerIndex INT,
                    CHECK (
                        (QuizExamID IS NOT NULL AND ContestExamID IS NULL) OR
                        (ContestExamID IS NOT NULL AND QuizExamID IS NULL)
                    )
                );

                CREATE TYPE AssignmentStatus AS ENUM ('pending', 'submitted', 'graded', 'passed', 'failed');

                CREATE TABLE Assignment (
                    AssignmentID BIGSERIAL PRIMARY KEY,
                    Title VARCHAR(100) NOt NULL,
                    Description TEXT NOT NULL,
                    CourseSectionID INT REFERENCES CourseSection(CourseSectionID) ON DELETE CASCADE,
                    MaxMarks INT,
                    PassingMarks INT,
                    FileAttched TEXT, -- link to file attached
                    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE CourseAnnouncements (
                    AnnouncementID BIGSERIAL PRIMARY KEY,
                    AnnouncerID INT REFERENCES Instructor(InstructorID) ON DELETE SET NULL,
                    CourseID INT REFERENCES Course(CourseID) ON DELETE CASCADE NOT NULL,
                    Announcement TEXT
                );

                CREATE TABLE Student_Assignment (
                    StudentAssignmentID BIGSERIAL PRIMARY KEY,
                    StudentID INT REFERENCES Student(StudentID) ON DELETE CASCADE,
                    AssignmentID INT REFERENCES Assignment(AssignmentID) ON DELETE CASCADE,
                    SubmissionLink TEXT, -- Link to submitted assignment file, if applicable
                    Grade DECIMAL(5,2), -- Grade achieved on the assignment
                    Status AssignmentStatus DEFAULT 'pending',
                    SubmissionDate TIMESTAMP,
                    PassFail BOOLEAN -- true -> pass
                );

                CREATE TABLE Transactions (
                    TransactionID BIGSERIAL PRIMARY KEY,
                    StudentID INT REFERENCES Student(StudentID),
                    InstructorID INT REFERENCES Instructor(InstructorID),
                    Amount DECIMAL(10,2),
                    ExecutedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- CREATE TABLE Statistics (
                -- 	CourseID INT REFERENCES Course(CourseID),
                -- 	InstructorID INT REFERENCES Instructor(InstructorID),
                -- 	StudentCount INT,
                -- 	CompletionRate DECIMAL(4,2),
                -- 	AverageGrades DECIMAL(10,2)
                -- );

                CREATE TABLE InstructorWhiteBoard (
                    InstructorWhiteBoardID BIGSERIAL PRIMARY KEY,
                    InstructorID INT REFERENCES Instructor(InstructorID),
                    CourseID INT REFERENCES Course(CourseID),
                    AssignmentID INT REFERENCES Assignment(AssignmentID) ON DELETE CASCADE,
                    QuizExamID INT REFERENCES QuizExam(QuizExamID) ON DELETE CASCADE,
                    ContestExamID INT REFERENCES ContestExam(ContestExamID) ON DELETE CASCADE,
                    CHECK (
                        (QuizExamID IS NOT NULL AND ContestExamID IS NULL AND AssignmentID IS NULL) OR
                        (ContestExamID IS NOT NULL AND QuizExamID IS NULL AND AssignmentID IS NULL) OR
                        (ContestExamID IS NULL AND QuizExamID IS NULL AND AssignmentID IS NOT NULL)
                    )
                );
                -- revise below table
                CREATE TABLE FeedBack_Reviews (
                    ReviewID BIGSERIAL PRIMARY KEY,
                    CourseID INT REFERENCES Course(CourseID),
                    InstructorID INT REFERENCES Instructor(InstructorID),
                    Rating DECIMAL(3,2),
                    Review TEXT,
                    CHECK (
                        (CourseID IS NOT NULL AND InstructorID IS NULL) OR
                        (CourseID IS NULL AND InstructorID IS NOT NULL)
                    )
                );
            """
        )
    ]