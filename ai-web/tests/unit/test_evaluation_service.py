"""
Unit tests for EvaluationService
"""
import pytest
from app.services.evaluation_service import EvaluationService
from app.models.manual_evaluation import ManualEvaluation
from app.models.training_video import TrainingVideo
from app.models.assignment import Assignment


class TestEvaluationService:
    """Test EvaluationService methods"""

    def test_create_evaluation_success(self, db_session, instructor_user, sample_routine, sample_user):
        """Test creating manual evaluation"""
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
        db_session.commit()

        data = {
            'overall_score': 85,
            'technique_score': 80,
            'posture_score': 85,
            'spirit_score': 90,
            'comments': 'Good performance',
            'is_passed': True
        }

        result = EvaluationService.create_evaluation(video.video_id, instructor_user.user_id, data)

        assert result['success'] == True
        assert result['evaluation'].overall_score == 85
        assert result['evaluation'].is_passed == True

    def test_create_evaluation_video_not_found(self, db_session, instructor_user):
        """Test creating evaluation for non-existent video fails"""
        data = {
            'overall_score': 85,
            'is_passed': True
        }

        result = EvaluationService.create_evaluation(99999, instructor_user.user_id, data)

        assert result['success'] == False
        assert 'không tìm thấy' in result['message'].lower() or 'not found' in result['message'].lower()

    def test_create_evaluation_duplicate_fails(self, db_session, instructor_user, sample_routine, sample_user):
        """Test creating duplicate evaluation fails"""
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
        db_session.commit()

        data = {
            'overall_score': 85,
            'is_passed': True
        }

        # Create first evaluation
        EvaluationService.create_evaluation(video.video_id, instructor_user.user_id, data)

        # Try to create duplicate
        result = EvaluationService.create_evaluation(video.video_id, instructor_user.user_id, data)

        assert result['success'] == False
        assert 'đã chấm' in result['message'].lower() or 'already' in result['message'].lower()

    def test_get_evaluation_by_video(self, db_session, instructor_user, sample_routine, sample_user):
        """Test getting evaluation by video"""
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
        db_session.commit()

        data = {
            'overall_score': 85,
            'is_passed': True
        }

        EvaluationService.create_evaluation(video.video_id, instructor_user.user_id, data)

        evaluations = EvaluationService.get_evaluation_by_video(video.video_id)

        assert len(evaluations) >= 1
        assert evaluations[0].overall_score == 85

    def test_get_evaluation_for_instructor(self, db_session, instructor_user, sample_routine, sample_user):
        """Test getting evaluation for specific instructor"""
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
        db_session.commit()

        data = {
            'overall_score': 85,
            'is_passed': True
        }

        EvaluationService.create_evaluation(video.video_id, instructor_user.user_id, data)

        evaluation = EvaluationService.get_evaluation_for_instructor(video.video_id, instructor_user.user_id)

        assert evaluation is not None
        assert evaluation.overall_score == 85

    def test_update_evaluation_success(self, db_session, instructor_user, sample_routine, sample_user):
        """Test updating evaluation"""
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
        db_session.commit()

        # Create evaluation
        data1 = {
            'overall_score': 80,
            'is_passed': True
        }
        create_result = EvaluationService.create_evaluation(video.video_id, instructor_user.user_id, data1)
        evaluation = create_result['evaluation']

        # Update evaluation
        data2 = {
            'overall_score': 90,
            'technique_score': 85,
            'posture_score': 90,
            'spirit_score': 95,
            'comments': 'Excellent performance',
            'is_passed': True
        }

        result = EvaluationService.update_evaluation(evaluation, data2)

        assert result['success'] == True
        assert result['evaluation'].overall_score == 90
        assert result['evaluation'].comments == 'Excellent performance'

    def test_get_pending_submissions(self, db_session, instructor_user, sample_routine, sample_user, approved_class):
        """Test getting pending submissions"""
        # Enroll student in class
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

        # Create video without evaluation
        video = TrainingVideo(
            student_id=sample_user.user_id,
            assignment_id=assignment.assignment_id,
            routine_id=sample_routine.routine_id,
            video_url='/static/uploads/video.mp4',
            processing_status='completed'
        )
        db_session.add(video)
        db_session.commit()

        pending = EvaluationService.get_pending_submissions(instructor_user.user_id)

        assert len(pending) >= 1
        assert video in pending

    def test_get_all_submissions(self, db_session, instructor_user, sample_routine, sample_user, approved_class):
        """Test getting all submissions"""
        # Enroll student in class
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

        # Create video
        video = TrainingVideo(
            student_id=sample_user.user_id,
            assignment_id=assignment.assignment_id,
            routine_id=sample_routine.routine_id,
            video_url='/static/uploads/video.mp4',
            processing_status='completed'
        )
        db_session.add(video)
        db_session.commit()

        all_submissions = EvaluationService.get_all_submissions(instructor_user.user_id)

        assert len(all_submissions) >= 1
        assert video in all_submissions

