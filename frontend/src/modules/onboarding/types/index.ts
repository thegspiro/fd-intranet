/**
 * Onboarding Module Types
 */

export interface OnboardingData {
  // Department Information
  departmentName: string;
  hasLogo: boolean;
  logoData?: string;

  // Navigation Layout
  navigationLayout: 'top' | 'left' | null;

  // Email Configuration
  emailPlatform: 'gmail' | 'microsoft' | 'selfhosted' | 'other' | null;
  emailConfig?: EmailConfig;
  emailConfigMethod?: 'oauth' | 'apppassword';

  // File Storage Configuration
  fileStoragePlatform: 'googledrive' | 'onedrive' | 's3' | 'local' | 'other' | null;
  fileStorageConfig?: FileStorageConfig;

  // Admin User
  adminUser?: AdminUser;
}

export interface EmailConfig {
  // Gmail OAuth
  googleClientId?: string;
  googleClientSecret?: string;
  googleAppPassword?: string;
  googleEmail?: string;

  // Microsoft 365
  microsoftTenantId?: string;
  microsoftClientId?: string;
  microsoftClientSecret?: string;

  // Self-hosted SMTP
  smtpHost?: string;
  smtpPort?: number;
  smtpEncryption?: 'tls' | 'ssl' | 'none';
  smtpUsername?: string;
  smtpPassword?: string;

  // Common fields
  fromEmail: string;
  fromName?: string;
}

export interface FileStorageConfig {
  // Google Drive
  googleDriveClientId?: string;
  googleDriveClientSecret?: string;
  googleDriveFolderId?: string;

  // OneDrive / SharePoint
  oneDriveTenantId?: string;
  oneDriveClientId?: string;
  oneDriveClientSecret?: string;
  sharePointSiteUrl?: string;
  sharePointLibraryName?: string;

  // Amazon S3
  s3AccessKeyId?: string;
  s3SecretAccessKey?: string;
  s3BucketName?: string;
  s3Region?: string;

  // Local Storage
  localStoragePath?: string;
}

export interface AdminUser {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  badgeNumber?: string;
  password: string;
  confirmPassword: string;
}

export interface OnboardingStatus {
  isCompleted: boolean;
  currentStep: number;
  stepsCompleted: Record<string, boolean>;
}

export type OnboardingStep =
  | 'welcome'
  | 'department-info'
  | 'navigation-choice'
  | 'email-platform'
  | 'email-config'
  | 'file-storage-choice'
  | 'file-storage-config'
  | 'admin-user'
  | 'security-check'
  | 'complete';

export interface PasswordStrength {
  checks: {
    length: boolean;
    uppercase: boolean;
    lowercase: boolean;
    number: boolean;
    special: boolean;
  };
  passedChecks: number;
}
