# fd-intranet/management/commands/load_initial_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction

# Import models from core apps
from compliance.models import GroupProfile
from accounts.models import Certification
from scheduling.models import ShiftType, ShiftPosition
from fd_intranet.settings import AUTH_USER_MODEL # Ensure the custom user model is used

class Command(BaseCommand):
    help = 'Loads initial required system groups, certifications, and shift positions.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('--- Starting Initial Data Load ---'))

        # --- 1. Create Core Administrative and Operational Roles (Django Groups) ---
        self.stdout.write('\n-> Creating system roles...')
        
        # Define roles and their attributes (is_temporary, max_duration_days)
        ROLES_TO_CREATE = {
            'Chief': {'is_temporary': False, 'max_days': 0},
            'President': {'is_temporary': False, 'max_days': 0},
            'Secretary': {'is_temporary': False, 'max_days': 0},
            'Compliance Officer': {'is_temporary': False, 'max_days': 0},
            'Scheduler': {'is_temporary': False, 'max_days': 0},
            'Quartermaster': {'is_temporary': False, 'max_days': 0},
            'Firefighter': {'is_temporary': False, 'max_days': 0},
            
            # Time-bound role requiring the safety net monitor
            'Probationary Member': {'is_temporary': True, 'max_days': 365, 'emails': 'chief@dept.org, compliance@dept.org'},
            
            'Driver': {'is_temporary': False, 'max_days': 0},
            'Attendant In Charge (AIC)': {'is_temporary': False, 'max_days': 0},
        }

        created_groups = 0
        for name, attrs in ROLES_TO_CREATE.items():
            try:
                with transaction.atomic():
                    group, created = Group.objects.get_or_create(name=name)
                    if created:
                        # Create the associated GroupProfile for the safety net monitor
                        GroupProfile.objects.create(
                            group=group,
                            is_temporary=attrs['is_temporary'],
                            max_duration_days=attrs['max_days'],
                            warning_email_list=attrs.get('emails', '')
                        )
                        self.stdout.write(f'  Created Group: {name}')
                        created_groups += 1
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f'  Error creating {name}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created/updated {created_groups} groups.'))


        # --- 2. Create Core Certifications (Compliance Requirements) ---
        self.stdout.write('\n-> Creating default certifications...')
        CERTIFICATIONS = ['CPR/AED', 'First Aid', 'Driver Operator', 'Firefighter I', 'NIMS 700/800']
        created_certs = 0
        
        for name in CERTIFICATIONS:
            try:
                Certification.objects.get_or_create(name=name)
                created_certs += 1
            except IntegrityError:
                pass
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created/updated {created_certs} certifications.'))


        # --- 3. Create Default Shift Types ---
        self.stdout.write('\n-> Creating default shift types...')
        SHIFT_TYPES = [
            {'name': 'Operational Coverage', 'is_coverage_shift': True},
            {'name': 'Mandatory Training', 'is_coverage_shift': False},
            {'name': 'Administrative Duty', 'is_coverage_shift': False},
        ]
        created_shift_types = 0
        
        for data in SHIFT_TYPES:
            ShiftType.objects.get_or_create(**data)
            created_shift_types += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created/updated {created_shift_types} shift types.'))


        # --- 4. Create Default Shift Positions (Requires certs/roles created above) ---
        self.stdout.write('\n-> Creating default shift positions...')
        
        # Fetch the previously created roles/certs for linking
        driver_role = Group.objects.get(name='Driver')
        aic_role = Group.objects.get(name='Attendant In Charge (AIC)')
        driver_cert = Certification.objects.get(name='Driver Operator')
        
        
        POSITIONS_TO_CREATE = [
            {'name': 'Shift Firefighter', 'required_roles': ['Firefighter']},
            {'name': 'Primary Driver', 'required_roles': ['Driver'], 'required_certs': ['Driver Operator']},
            {'name': 'Attendant In Charge (AIC)', 'required_roles': ['Attendant In Charge (AIC)']},
            {'name': 'EMS Third', 'required_roles': ['Firefighter'], 'required_certs': ['CPR/AED']},
        ]
        created_positions = 0
        
        for data in POSITIONS_TO_CREATE:
            position, created = ShiftPosition.objects.get_or_create(name=data['name'])
            
            if created:
                # Link required roles
                for role_name in data.get('required_roles', []):
                    role = Group.objects.get(name=role_name)
                    position.required_roles.add(role)
                
                # Link required certifications
                for cert_name in data.get('required_certs', []):
                    cert = Certification.objects.get(name=cert_name)
                    position.required_certifications.add(cert)
                
                position.save()
                created_positions += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully created/updated {created_positions} shift positions.'))


        self.stdout.write(self.style.SUCCESS('\n--- INITIAL DATA LOAD COMPLETE. Platform is ready for use. ---'))
        self.stdout.write(self.style.WARNING('Remember to run "python manage.py createsuperuser" if you have not already.'))
