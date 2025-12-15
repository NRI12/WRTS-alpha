from datetime import datetime
from app.utils.helpers import get_vietnam_time

class ReportService:
    
    @staticmethod
    def generate_class_report(class_id):
        """Tạo báo cáo lớp học (dạng dict - có thể export PDF/Excel)"""
        from app.models.class_model import Class
        from app.services.analytics_service import AnalyticsService
        
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return None
        
        overview = AnalyticsService.get_class_overview(class_id)
        rankings = AnalyticsService.get_student_ranking(class_id)
        
        report = {
            'generated_at': get_vietnam_time().isoformat(),
            'class_info': {
                'name': class_obj.class_name,
                'code': class_obj.class_code,
                'instructor': class_obj.instructor.full_name,
                'level': class_obj.level,
                'start_date': str(class_obj.start_date)
            },
            'overview': overview,
            'student_rankings': [
                {
                    'name': r['student'].full_name,
                    'avg_score': r['avg_score'],
                    'videos': r['video_count']
                }
                for r in rankings
            ]
        }
        
        return report
    
    @staticmethod
    def generate_system_report():
        """Tạo báo cáo toàn hệ thống"""
        from app.services.analytics_service import AnalyticsService
        
        overview = AnalyticsService.get_system_overview()
        instructor_perf = AnalyticsService.get_instructor_performance()
        
        report = {
            'generated_at': get_vietnam_time().isoformat(),
            'system_overview': overview,
            'instructor_performance': [
                {
                    'name': p['instructor'].full_name,
                    'classes': p['total_classes'],
                    'students': p['total_students'],
                    'avg_score': p['avg_student_score']
                }
                for p in instructor_perf
            ]
        }
        
        return report
