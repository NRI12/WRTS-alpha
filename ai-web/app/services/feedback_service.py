from app.models import db
from app.models.feedback import Feedback
from app.utils.helpers import get_vietnam_time
from datetime import datetime, timedelta
from sqlalchemy import func

class FeedbackService:
    
    @staticmethod
    def create_feedback(user_id, data):
        """Tạo feedback mới"""
        feedback = Feedback(
            user_id=user_id,
            feedback_type=data['feedback_type'],
            subject=data['subject'],
            content=data['content'],
            priority='normal',
            feedback_status='pending'
        )
        
        db.session.add(feedback)
        db.session.commit()
        return {'success': True, 'feedback': feedback}
    
    @staticmethod
    def get_all_feedback(filters=None):
        """Lấy tất cả feedback với filter"""
        query = Feedback.query
        
        if filters:
            if filters.get('status'):
                query = query.filter_by(feedback_status=filters['status'])
            if filters.get('type'):
                query = query.filter_by(feedback_type=filters['type'])
            if filters.get('priority'):
                query = query.filter_by(priority=filters['priority'])
        
        return query.order_by(Feedback.created_at.desc()).all()
    
    @staticmethod
    def get_feedback_by_id(feedback_id):
        """Lấy feedback theo ID"""
        return Feedback.query.get(feedback_id)
    
    @staticmethod
    def update_feedback(feedback_id, data):
        """Cập nhật feedback"""
        feedback = Feedback.query.get(feedback_id)
        if not feedback:
            return {'success': False, 'message': 'Không tìm thấy phản hồi'}
        
        feedback.priority = data.get('priority', feedback.priority)
        feedback.feedback_status = data.get('feedback_status', feedback.feedback_status)
        feedback.resolution_notes = data.get('resolution_notes', feedback.resolution_notes)
        feedback.updated_at = get_vietnam_time()
        
        if data.get('feedback_status') in ['resolved', 'rejected', 'implemented']:
            feedback.resolved_at = get_vietnam_time()
        
        db.session.commit()
        return {'success': True, 'feedback': feedback}
    
    @staticmethod
    def get_user_feedback(user_id):
        """Lấy feedback của user"""
        return Feedback.query.filter_by(user_id=user_id).order_by(
            Feedback.created_at.desc()
        ).all()
    
    @staticmethod
    def get_total_feedback_count():
        """Get total number of feedback"""
        return Feedback.query.count()
    
    @staticmethod
    def get_feedback_count_by_status(status):
        """Get count of feedback by status"""
        # Map common status names to enum values
        status_map = {
            'pending': 'pending',
            'in_progress': 'in_review', 
            'resolved': 'resolved',
            'closed': 'implemented'
        }
        actual_status = status_map.get(status, status)
        return Feedback.query.filter_by(feedback_status=actual_status).count()
    
    @staticmethod
    def get_recent_feedback(days=None, limit=10):
        """Get recent feedback"""
        query = Feedback.query
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.filter(Feedback.created_at >= cutoff_date)
        
        return query.order_by(Feedback.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_feedback_stats():
        """Get feedback statistics"""
        stats = db.session.query(
            Feedback.feedback_status,
            func.count(Feedback.feedback_id).label('count')
        ).group_by(Feedback.feedback_status).all()
        
        return {stat.feedback_status: stat.count for stat in stats}
