"""
Target Solutions / Vector Solutions API Integration
Syncs training records, certifications, and course completions
"""
import requests
import logging
from django.conf import settings
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TargetSolutionsClient:
    """
    Client for Target Solutions API
    Documentation: https://developer.targetsolutions.com
    """
    
    def __init__(self):
        self.base_url = settings.TARGET_SOLUTIONS_BASE_URL
        self.api_key = settings.TARGET_SOLUTIONS_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.timeout = 30
    
    def _make_request(self, endpoint: str, method: str = 'GET', 
                     data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make authenticated API request
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, PUT, DELETE)
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dict, or None on error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=self.timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
        
        except requests.exceptions.Timeout:
            logger.error(f"Target Solutions API timeout: {endpoint}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Target Solutions API error on {endpoint}: {e}")
        except ValueError as e:
            logger.error(f"Invalid JSON response from {endpoint}: {e}")
        
        return None
    
    # --- User/Member Management ---
    
    def get_users(self, page: int = 1, per_page: int = 100) -> Optional[List[Dict]]:
        """
        Get list of users from Target Solutions
        
        Args:
            page: Page number for pagination
            per_page: Number of results per page
            
        Returns:
            List of user dictionaries
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        response = self._make_request('api/v1/users', params=params)
        return response.get('users', []) if response else None
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """
        Get details for a specific user
        
        Args:
            user_id: Target Solutions user ID
            
        Returns:
            User data dictionary
        """
        return self._make_request(f'api/v1/users/{user_id}')
    
    def create_user(self, user_data: Dict) -> Optional[Dict]:
        """
        Create a new user in Target Solutions
        
        Args:
            user_data: Dictionary containing user information
                Required fields: first_name, last_name, email
                
        Returns:
            Created user data
        """
        return self._make_request('api/v1/users', method='POST', data=user_data)
    
    def update_user(self, user_id: str, user_data: Dict) -> Optional[Dict]:
        """
        Update an existing user
        
        Args:
            user_id: Target Solutions user ID
            user_data: Updated user information
            
        Returns:
            Updated user data
        """
        return self._make_request(f'api/v1/users/{user_id}', method='PUT', data=user_data)
    
    # --- Course Management ---
    
    def get_courses(self, active_only: bool = True) -> Optional[List[Dict]]:
        """
        Get list of available courses
        
        Args:
            active_only: Only return active courses
            
        Returns:
            List of course dictionaries
        """
        params = {'active': active_only}
        response = self._make_request('api/v1/courses', params=params)
        return response.get('courses', []) if response else None
    
    def get_course(self, course_id: str) -> Optional[Dict]:
        """
        Get details for a specific course
        
        Args:
            course_id: Target Solutions course ID
            
        Returns:
            Course data dictionary
        """
        return self._make_request(f'api/v1/courses/{course_id}')
    
    # --- Training Records / Completions ---
    
    def get_user_completions(self, user_id: str, start_date: str = None, 
                            end_date: str = None) -> Optional[List[Dict]]:
        """
        Get training completions for a specific user
        
        Args:
            user_id: Target Solutions user ID
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            
        Returns:
            List of completion records
        """
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        response = self._make_request(f'api/v1/users/{user_id}/completions', params=params)
        return response.get('completions', []) if response else None
    
    def create_completion(self, user_id: str, completion_data: Dict) -> Optional[Dict]:
        """
        Record a course completion for a user
        
        Args:
            user_id: Target Solutions user ID
            completion_data: Dictionary with completion information
                Required fields: course_id, completion_date
                Optional: score, hours, instructor_id
                
        Returns:
            Created completion record
        """
        return self._make_request(
            f'api/v1/users/{user_id}/completions',
            method='POST',
            data=completion_data
        )
    
    # --- Certifications ---
    
    def get_user_certifications(self, user_id: str) -> Optional[List[Dict]]:
        """
        Get certifications for a specific user
        
        Args:
            user_id: Target Solutions user ID
            
        Returns:
            List of certification records
        """
        response = self._make_request(f'api/v1/users/{user_id}/certifications')
        return response.get('certifications', []) if response else None
    
    def create_certification(self, user_id: str, cert_data: Dict) -> Optional[Dict]:
        """
        Record a certification for a user
        
        Args:
            user_id: Target Solutions user ID
            cert_data: Dictionary with certification information
                Required: certification_type, issue_date
                Optional: expiration_date, certification_number
                
        Returns:
            Created certification record
        """
        return self._make_request(
            f'api/v1/users/{user_id}/certifications',
            method='POST',
            data=cert_data
        )
    
    # --- Assignments ---
    
    def assign_course(self, user_id: str, course_id: str, 
                     due_date: str = None) -> Optional[Dict]:
        """
        Assign a course to a user
        
        Args:
            user_id: Target Solutions user ID
            course_id: Course to assign
            due_date: Optional due date (YYYY-MM-DD)
            
        Returns:
            Assignment record
        """
        data = {
            'course_id': course_id,
            'user_id': user_id
        }
        if due_date:
            data['due_date'] = due_date
        
        return self._make_request('api/v1/assignments', method='POST', data=data)
    
    def get_user_assignments(self, user_id: str, 
                            include_completed: bool = False) -> Optional[List[Dict]]:
        """
        Get course assignments for a user
        
        Args:
            user_id: Target Solutions user ID
            include_completed: Include completed assignments
            
        Returns:
            List of assignment records
        """
        params = {'include_completed': include_completed}
        response = self._make_request(f'api/v1/users/{user_id}/assignments', params=params)
        return response.get('assignments', []) if response else None
    
    # --- Reports ---
    
    def get_training_report(self, start_date: str, end_date: str, 
                           user_ids: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Get training report for date range
        
        Args:
            start_date: Report start date (YYYY-MM-DD)
            end_date: Report end date (YYYY-MM-DD)
            user_ids: Optional list of specific user IDs to include
            
        Returns:
            Report data dictionary
        """
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        if user_ids:
            params['user_ids'] = ','.join(user_ids)
        
        return self._make_request('api/v1/reports/training', params=params)
    
    def get_compliance_report(self, certification_type: str = None) -> Optional[Dict]:
        """
        Get compliance status report
        
        Args:
            certification_type: Optional filter by certification type
            
        Returns:
            Compliance report data
        """
        params = {}
        if certification_type:
            params['certification_type'] = certification_type
        
        return self._make_request('api/v1/reports/compliance', params=params)


class TargetSolutionsSyncService:
    """
    Service for syncing data between FD Intranet and Target Solutions
    """
    
    def __init__(self):
        self.client = TargetSolutionsClient()
    
    def sync_user_to_target_solutions(self, user):
        """
        Create or update a user in Target Solutions
        
        Args:
            user: Django User object
            
        Returns:
            Target Solutions user ID
        """
        from accounts.models import UserProfile
        
        try:
            profile = user.userprofile
        except UserProfile.DoesNotExist:
            logger.error(f"No profile found for user {user.username}")
            return None
        
        # Check if user already exists in Target Solutions
        # (You'd need to store the Target Solutions ID in your UserProfile)
        ts_user_id = getattr(profile, 'target_solutions_id', None)
        
        user_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'badge_number': profile.badge_number,
            'phone': profile.phone_number
        }
        
        if ts_user_id:
            # Update existing user
            result = self.client.update_user(ts_user_id, user_data)
        else:
            # Create new user
            result = self.client.create_user(user_data)
            if result and 'id' in result:
                # Store the Target Solutions ID
                profile.target_solutions_id = result['id']
                profile.save()
        
        return result.get('id') if result else None
    
    def sync_completions_from_target_solutions(self, user, ts_user_id: str, 
                                              start_date: str = None):
        """
        Import training completions from Target Solutions
        
        Args:
            user: Django User object
            ts_user_id: Target Solutions user ID
            start_date: Only import completions after this date
            
        Returns:
            Number of records imported
        """
        from training.models import TrainingRequirement, TrainingRecord
        
        completions = self.client.get_user_completions(ts_user_id, start_date=start_date)
        
        if not completions:
            return 0
        
        imported_count = 0
        
        for completion in completions:
            try:
                # Find matching training requirement by Target Solutions course ID
                requirement = TrainingRequirement.objects.get(
                    target_solutions_id=completion['course_id']
                )
                
                completion_date = datetime.strptime(
                    completion['completion_date'], 
                    '%Y-%m-%d'
                ).date()
                
                # Check if record already exists
                existing = TrainingRecord.objects.filter(
                    user=user,
                    requirement=requirement,
                    completion_date=completion_date
                ).first()
                
                if not existing:
                    TrainingRecord.objects.create(
                        user=user,
                        requirement=requirement,
                        completion_date=completion_date,
                        verification_status='APPROVED',
                        hours_completed=completion.get('hours', 0),
                        notes=f"Imported from Target Solutions on {datetime.now().date()}"
                    )
                    imported_count += 1
            
            except TrainingRequirement.DoesNotExist:
                logger.warning(
                    f"No matching requirement for Target Solutions course {completion['course_id']}"
                )
            except Exception as e:
                logger.error(f"Error importing completion: {e}")
        
        logger.info(f"Imported {imported_count} training records for {user.get_full_name()}")
        return imported_count
    
    def sync_all_users(self):
        """
        Sync all active users to Target Solutions
        
        Returns:
            Number of users synced
        """
        from django.contrib.auth.models import User
        
        active_users = User.objects.filter(is_active=True)
        synced_count = 0
        
        for user in active_users:
            result = self.sync_user_to_target_solutions(user)
            if result:
                synced_count += 1
        
        logger.info(f"Synced {synced_count} users to Target Solutions")
        return synced_count
