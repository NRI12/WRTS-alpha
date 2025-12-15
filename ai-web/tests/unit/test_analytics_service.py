"""
Unit tests for AnalyticsService
"""
import pytest
from app.services.analytics_service import AnalyticsService
from app.models.training_video import TrainingVideo
from app.models.manual_evaluation import ManualEvaluation
from app.models.assignment import Assignment


class TestAnalyticsService:
    """Test AnalyticsService methods"""

    def test_get_student_overview(self, db_session, sample_user, instructor_user, sample_routine):
        """Test getting student overview"""
        # Create assignment and video with evaluation
        assignment = Assignment(
            routine_id=sample_routine.routine_id,
            assigned_by=instructor_user.user_id,
            assignment_type='individual',
            assigned_to_student=sample_user.user_id,
            instructor_video_url='/static/uploads/demo.mp4',
            grading_method='manual'
        )
        db_session.add(assignment)
        db_session.flush()

        video = TrainingVideo(
            student_id=sample_user.user_id,
            assignment_id=assignment.assignment_id,
            routine_id=sample_routine.routine_id,
            video_url='/static/uploads/video.mp4',
            processing_status='completed'
        )
        db_session.add(video)
        db_session.flush()

        evaluation = ManualEvaluation(
            video_id=video.video_id,
            instructor_id=instructor_user.user_id,
            overall_score=85,
            is_passed=True,
            evaluation_method='manual'
        )
        db_session.add(evaluation)
        db_session.commit()

        overview = AnalyticsService.get_student_overview(sample_user.user_id)

        assert 'total_videos' in overview
        assert 'avg_manual_score' in overview
        assert 'passed_count' in overview
        assert 'pass_rate' in overview
        assert overview['total_videos'] >= 1
        assert overview['avg_manual_score'] > 0

    def test_get_score_progression(self, db_session, sample_user, instructor_user, sample_routine):
        """Test getting score progression"""
        # Create assignment and video
        assignment = Assignment(
            routine_id=sample_routine.routine_id,
            assigned_by=instructor_user.user_id,
            assignment_type='individual',
            assigned_to_student=sample_user.user_id,
            instructor_video_url='/static/uploads/demo.mp4',
            grading_method='manual'
        )
        db_session.add(assignment)
        db_session.flush()

        video = TrainingVideo(
            student_id=sample_user.user_id,
            assignment_id=assignment.assignment_id,
            routine_id=sample_routine.routine_id,
            video_url='/static/uploads/video.mp4',
            processing_status='completed'
        )
        db_session.add(video)
        db_session.flush()

        evaluation = ManualEvaluation(
            video_id=video.video_id,
            instructor_id=instructor_user.user_id,
            overall_score=85,
            is_passed=True,
            evaluation_method='manual'
        )
        db_session.add(evaluation)
        db_session.commit()

        progression = AnalyticsService.get_score_progression(sample_user.user_id, days=30)

        assert len(progression) >= 1
        assert 'date' in progression[0]
        assert 'manual_score' in progression[0]

    def test_get_routine_completion(self, db_session, sample_user, sample_routine):
        """Test getting routine completion"""
        completion = AnalyticsService.get_routine_completion(sample_user.user_id)

        assert 'total_routines' in completion
        assert 'completed' in completion
        assert 'completion_rate' in completion

    def test_get_strengths_weaknesses(self, db_session, sample_user, instructor_user, sample_routine):
        """Test getting strengths and weaknesses"""
        # Create assignment and video with detailed evaluation
        assignment = Assignment(
            routine_id=sample_routine.routine_id,
            assigned_by=instructor_user.user_id,
            assignment_type='individual',
            assigned_to_student=sample_user.user_id,
            instructor_video_url='/static/uploads/demo.mp4',
            grading_method='manual'
        )
        db_session.add(assignment)
        db_session.flush()

        video = TrainingVideo(
            student_id=sample_user.user_id,
            assignment_id=assignment.assignment_id,
            routine_id=sample_routine.routine_id,
            video_url='/static/uploads/video.mp4',
            processing_status='completed'
        )
        db_session.add(video)
        db_session.flush()

        evaluation = ManualEvaluation(
            video_id=video.video_id,
            instructor_id=instructor_user.user_id,
            overall_score=85,
            technique_score=80,
            posture_score=85,
            spirit_score=90,
            is_passed=True,
            evaluation_method='manual'
        )
        db_session.add(evaluation)
        db_session.commit()

        strengths = AnalyticsService.get_strengths_weaknesses(sample_user.user_id)

        assert 'technique' in strengths
        assert 'posture' in strengths
        assert 'spirit' in strengths

    def test_get_class_overview(self, db_session, approved_class, sample_user, instructor_user, sample_routine):
        """Test getting class overview"""
        # Enroll student
        from app.services.class_service import ClassService
        ClassService.enroll_student(approved_class.class_id, sample_user.user_id)

        # Create assignment
        assignment = Assignment(
            routine_id=sample_routine.routine_id,
            assigned_by=instructor_user.user_id,
            assignment_type='class',
            assigned_to_class=approved_class.class_id,
            instructor_video_url='/static/uploads/demo.mp4',
            grading_method='manual'
        )
        db_session.add(assignment)
        db_session.flush()

        # Create video with evaluation
        video = TrainingVideo(
            student_id=sample_user.user_id,
            assignment_id=assignment.assignment_id,
            routine_id=sample_routine.routine_id,
            video_url='/static/uploads/video.mp4',
            processing_status='completed'
        )
        db_session.add(video)
        db_session.flush()

        evaluation = ManualEvaluation(
            video_id=video.video_id,
            instructor_id=instructor_user.user_id,
            overall_score=85,
            is_passed=True,
            evaluation_method='manual'
        )
        db_session.add(evaluation)
        db_session.commit()

        overview = AnalyticsService.get_class_overview(approved_class.class_id)

        assert 'total_students' in overview
        assert 'avg_score' in overview
        assert 'total_submissions' in overview
        assert 'pass_rate' in overview
        assert overview['total_students'] >= 1

    def test_get_student_ranking(self, db_session, approved_class, sample_user, instructor_user, sample_routine):
        """Test getting student ranking"""
        # Enroll student
        from app.services.class_service import ClassService
        ClassService.enroll_student(approved_class.class_id, sample_user.user_id)

        # Create assignment and video with evaluation
        assignment = Assignment(
            routine_id=sample_routine.routine_id,
            assigned_by=instructor_user.user_id,
            assignment_type='class',
            assigned_to_class=approved_class.class_id,
            instructor_video_url='/static/uploads/demo.mp4',
            grading_method='manual'
        )
        db_session.add(assignment)
        db_session.flush()

        video = TrainingVideo(
            student_id=sample_user.user_id,
            assignment_id=assignment.assignment_id,
            routine_id=sample_routine.routine_id,
            video_url='/static/uploads/video.mp4',
            processing_status='completed'
        )
        db_session.add(video)
        db_session.flush()

        evaluation = ManualEvaluation(
            video_id=video.video_id,
            instructor_id=instructor_user.user_id,
            overall_score=85,
            is_passed=True,
            evaluation_method='manual'
        )
        db_session.add(evaluation)
        db_session.commit()

        rankings = AnalyticsService.get_student_ranking(approved_class.class_id)

        assert len(rankings) >= 1
        assert 'student' in rankings[0]
        assert 'avg_score' in rankings[0]
        assert 'video_count' in rankings[0]

    def test_get_system_overview(self, db_session):
        """Test getting system overview"""
        overview = AnalyticsService.get_system_overview()

        assert 'total_students' in overview
        assert 'total_instructors' in overview
        assert 'total_classes' in overview
        assert 'total_videos' in overview
        assert 'system_pass_rate' in overview

    def test_get_instructor_performance(self, db_session, instructor_user):
        """Test getting instructor performance"""
        performance = AnalyticsService.get_instructor_performance()

        assert len(performance) >= 1
        assert 'instructor' in performance[0]
        assert 'total_classes' in performance[0]
        assert 'total_students' in performance[0]
        assert 'avg_student_score' in performance[0]

    def test_get_trends_data(self, db_session):
        """Test getting trends data"""
        trends = AnalyticsService.get_trends_data(days=30)

        assert 'videos' in trends
        assert 'evaluations' in trends
        assert isinstance(trends['videos'], list)
        assert isinstance(trends['evaluations'], list)

