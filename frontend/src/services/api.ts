/**
 * API Service
 *
 * Handles all API calls to the backend.
 */

import axios from 'axios';
import type { User, ContactInfoSettings } from '../types/user';
import type {
  Role,
  Permission,
  PermissionCategory,
  UserWithRoles,
  RoleAssignment,
  UserRoleResponse
} from '../types/role';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const userService = {
  /**
   * Get all users/members in the organization
   */
  async getUsers(): Promise<User[]> {
    const response = await api.get<User[]>('/users');
    return response.data;
  },

  /**
   * Check if contact information is enabled
   */
  async checkContactInfoEnabled(): Promise<ContactInfoSettings> {
    const response = await api.get<ContactInfoSettings>('/users/contact-info-enabled');
    return response.data;
  },

  /**
   * Get all users with their assigned roles
   */
  async getUsersWithRoles(): Promise<UserWithRoles[]> {
    const response = await api.get<UserWithRoles[]>('/users/with-roles');
    return response.data;
  },

  /**
   * Get roles for a specific user
   */
  async getUserRoles(userId: string): Promise<UserRoleResponse> {
    const response = await api.get<UserRoleResponse>(`/users/${userId}/roles`);
    return response.data;
  },

  /**
   * Assign roles to a user (replaces existing roles)
   */
  async assignUserRoles(userId: string, roleIds: string[]): Promise<UserRoleResponse> {
    const response = await api.put<UserRoleResponse>(`/users/${userId}/roles`, {
      role_ids: roleIds,
    });
    return response.data;
  },

  /**
   * Add a single role to a user
   */
  async addRoleToUser(userId: string, roleId: string): Promise<UserRoleResponse> {
    const response = await api.post<UserRoleResponse>(`/users/${userId}/roles/${roleId}`);
    return response.data;
  },

  /**
   * Remove a role from a user
   */
  async removeRoleFromUser(userId: string, roleId: string): Promise<UserRoleResponse> {
    const response = await api.delete<UserRoleResponse>(`/users/${userId}/roles/${roleId}`);
    return response.data;
  },
};

export const organizationService = {
  /**
   * Get organization settings
   */
  async getSettings(): Promise<{ contact_info_visibility: ContactInfoSettings }> {
    const response = await api.get('/organization/settings');
    return response.data;
  },

  /**
   * Update contact information settings (secretary only)
   */
  async updateContactInfoSettings(settings: ContactInfoSettings): Promise<ContactInfoSettings> {
    const response = await api.patch('/organization/settings/contact-info', settings);
    return response.data;
  },
};

export const roleService = {
  /**
   * Get all available permissions
   */
  async getPermissions(): Promise<Permission[]> {
    const response = await api.get<Permission[]>('/roles/permissions');
    return response.data;
  },

  /**
   * Get permissions grouped by category
   */
  async getPermissionsByCategory(): Promise<PermissionCategory[]> {
    const response = await api.get<PermissionCategory[]>('/roles/permissions/by-category');
    return response.data;
  },

  /**
   * Get all roles
   */
  async getRoles(): Promise<Role[]> {
    const response = await api.get<Role[]>('/roles');
    return response.data;
  },

  /**
   * Get a specific role by ID
   */
  async getRole(roleId: string): Promise<Role> {
    const response = await api.get<Role>(`/roles/${roleId}`);
    return response.data;
  },

  /**
   * Create a new custom role
   */
  async createRole(roleData: {
    name: string;
    slug: string;
    description?: string;
    permissions: string[];
    priority?: number;
  }): Promise<Role> {
    const response = await api.post<Role>('/roles', roleData);
    return response.data;
  },

  /**
   * Update a role
   */
  async updateRole(
    roleId: string,
    updates: {
      name?: string;
      description?: string;
      permissions?: string[];
      priority?: number;
    }
  ): Promise<Role> {
    const response = await api.patch<Role>(`/roles/${roleId}`, updates);
    return response.data;
  },

  /**
   * Delete a custom role
   */
  async deleteRole(roleId: string): Promise<void> {
    await api.delete(`/roles/${roleId}`);
  },
};
