import { defineStore } from 'pinia'
import { api } from '@/boot/axios.js'

export const useCountSessionStore = defineStore('countSession', {
  state: () => ({
    items: [], // Unified list: products or positions depending on type
    positionTree: [], // Store full tree for lazy loading (position mode)
    loading: false,
    sessionType: 'product', // 'product' or 'position'

    // Session management state
    currentSession: null,
    sessionData: {
      code: '',
      description: '',
      type: 'product',
      blind_mode: true,
      scheduled_start: null,
      scheduled_end: null,
      status: null,
    },
    assignments: [],
    initialAssignments: new Map(), // Map of assignment key -> status
  }),

  getters: {
    /**
     * Calculate coverage percentage based on assignments
     * @param {Set} assignedItemKeys - Set of assigned item keys
     */
    sessionCoverage: (state) => (assignedItemKeys) => {
      const total = state.sessionType === 'product'
        ? state.items.length
        : state.fullPositionTree.length || 0;

      if (total === 0) return 0;
      return (assignedItemKeys.size / total) * 100;
    },
  },

  actions: {
    /**
     * Set the session type (product or position)
     */
    setSessionType(type) {
      if (this.sessionType !== type) {
        this.sessionType = type;
        // Clear items when type changes
        this.items = [];
        this.fullPositionTree = [];
      }
    },

    /**
     * Load products from API
     */
    async loadProducts() {
      console.log('loadProducts');
      this.loading = true;
      try {
        const { data } = await api.get('/product', {
          params: { active_only: true, limit: null },
        });
        this.items = data;
        return data;
      } catch (error) {
        console.error('Error loading products:', error);
        this.items = [];
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Load positions from API
     * Attempts to load hierarchical tree first, falls back to flat list
     */
    async loadPositions() {
      console.log('loadPositions');
      this.loading = true;
      try {
        // Try to build tree structure using position hierarchy
        try {
          const { data: hierarchyData } = await api.get('/position-hierarchy', {
            params: { position_key: 'IN' },
          });

          if (hierarchyData && hierarchyData.length > 0) {
            // Store full tree - child component will handle all processing
            this.fullPositionTree = hierarchyData;
            this.items = []; // Clear flat list when we have tree
          } else {
            // Fallback: fetch flat list if hierarchy is empty
            await this.loadPositionsFlat();
          }
        } catch (hierarchyError) {
          console.warn('Could not load position hierarchy, using flat list:', hierarchyError);
          // Fallback: fetch flat list
          await this.loadPositionsFlat();
        }
      } catch (error) {
        console.error('Error loading positions:', error);
        this.items = [];
        this.fullPositionTree = [];
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Load positions as a flat list (fallback method)
     */
    async loadPositionsFlat() {
      const { data } = await api.get('/position', {
        params: { limit: null },
      });
      this.items = data;
      this.fullPositionTree = [];
    },

    /**
     * Main method to load items based on current session type
     */
    async loadItems() {
      console.log('loadItems', this.sessionType);
      if (this.sessionType === 'product') {
        await this.loadProducts();
      } else {
        await this.loadPositions();
      }
    },

    /**
     * Reset/clear all data
     */
    reset() {
      this.items = [];
      this.fullPositionTree = [];
      this.sessionType = 'product';
      this.loading = false;
    },

    /**
     * Initialize session data for create mode
     */
    initializeSession() {
      this.currentSession = null;
      this.sessionData = {
        code: '',
        description: '',
        type: 'product',
        blind_mode: true,
        scheduled_start: null,
        scheduled_end: null,
        status: null,
      };
      this.assignments = [];
      this.initialAssignments = new Map();
    },

    /**
     * Load session data from API for edit mode
     * @param {string} countSessionKey - The session key to load
     * @returns {Promise<void>}
     */
    async loadSessionData(countSessionKey) {
      if (!countSessionKey) return;

      this.loading = true;
      try {
        const { data } = await api.get(`/inventory/count-session/${countSessionKey}`);

        // Update session data
        this.currentSession = countSessionKey;
        this.sessionData = {
          code: data.code,
          description: data.description,
          type: data.type,
          blind_mode: data.blind_mode,
          scheduled_start: data.scheduled_start,
          scheduled_end: data.scheduled_end,
          status: data.status,
        };

        // Process assignments
        const assignmentsByUser = [];
        const loadedAssignments = new Map();

        if (data.assignments) {
          for (const [userKey, userAssignments] of Object.entries(data.assignments)) {
            const assignment = {
              user_key: userKey,
              items: [],
            };

            for (const assign of userAssignments) {
              if (assign._key) {
                loadedAssignments.set(assign._key, assign.status);
              }
              assignment.items.push({
                _key: data.type === 'product' ? assign.target_key : undefined,
                key: data.type === 'position' ? assign.target_key : undefined,
                assignment_key: assign._key,
                code: assign.target_data?.code || assign.target_key,
                description: assign.target_data?.description || undefined,
                assignment_status: assign.status,
              });
            }

            assignmentsByUser.push(assignment);
          }
        }

        this.assignments = assignmentsByUser;
        this.initialAssignments = loadedAssignments;

        return data;
      } catch (error) {
        console.error('Error loading session data:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Create a new count session
     * @param {Array} assignmentsData - Assignments data
     * @returns {Promise<object>} Created session data
     */
    async createSession(assignmentsData = null) {
      const sessionPayload = {
        code: this.sessionData.code || null,
        description: this.sessionData.description || null,
        type: this.sessionData.type,
        blind_mode: this.sessionData.blind_mode,
        scheduled_start: this.sessionData.scheduled_start || null,
        scheduled_end: this.sessionData.scheduled_end || null,
      };

      const assignments = assignmentsData || this.assignments;

      const assignmentPayloads = assignments.map((assignment) => ({
        user_key: assignment.user_key,
        target_keys: assignment.items.map((item) => item._key || item.key),
      }));

      const { data: sessionResponse } = await api.post('/inventory/count-session', {
        count_session: sessionPayload,
        assignments: assignmentPayloads,
      });

      return sessionResponse;
    },

    /**
     * Update an existing count session
     * @param {string} countSessionKey - The session key to update
     * @param {Array} assignmentsData - Assignments data
     * @returns {Promise<void>}
     */
    async updateSession(countSessionKey, assignmentsData = null) {
      const sessionPayload = {};
      ['code', 'description', 'type', 'blind_mode', 'scheduled_start', 'scheduled_end'].forEach(field => {
        if (this.sessionData[field] !== undefined) {
          sessionPayload[field] = this.sessionData[field];
        }
      });

      await api.put(`/inventory/count-session/${countSessionKey}`, sessionPayload);

      // Manage assignments
      const assignments = assignmentsData || this.assignments;
      const assignmentsToDelete = [];
      const remainingKeys = new Set(this.initialAssignments.keys());
      const newAssignments = [];

      for (const assignment of assignments) {
        for (const item of assignment.items) {
          if (item.assignment_key) {
            if (remainingKeys.has(item.assignment_key)) {
              remainingKeys.delete(item.assignment_key);
            }
          } else {
            newAssignments.push({
              inventory_count_session_key: countSessionKey,
              assigned_to: assignment.user_key,
              target_key: item._key || item.key,
              target_type: this.sessionData.type,
            });
          }
        }
      }

      // Identify assignments to delete (only if they were 'planned')
      for (const key of remainingKeys) {
        if (this.initialAssignments.get(key) === 'planned') {
          assignmentsToDelete.push(key);
        }
      }

      if (assignmentsToDelete.length > 0) {
        await api.delete('/inventory/count-assignment', {
          data: { assignment_keys: assignmentsToDelete },
        });
      }

      if (newAssignments.length > 0) {
        await api.post('/inventory/count-assignment', newAssignments);
      }
    },

    /**
     * Save session (create or update based on currentSession)
     * @param {string|null} countSessionKey - The session key (null for create)
     * @param {Array} assignmentsData - Assignments data
     * @returns {Promise<object>} Session response
     */
    async saveSession(countSessionKey = null, assignmentsData = null) {
      const sessionKey = countSessionKey || this.currentSession;

      if (sessionKey) {
        await this.updateSession(sessionKey, assignmentsData);
        return { _key: sessionKey };
      } else {
        return await this.createSession(assignmentsData);
      }
    },

    /**
     * Delete assignments by keys
     * @param {Array<string>} assignmentKeys - Array of assignment keys to delete
     * @returns {Promise<void>}
     */
    async deleteAssignments(assignmentKeys) {
      if (assignmentKeys.length === 0) return;

      await api.delete('/inventory/count-assignment', {
        data: { assignment_keys: assignmentKeys },
      });
    },

    /**
     * Clear assignments (only planned ones)
     * Used when changing session type in edit mode
     * @returns {Promise<void>}
     */
    async clearPlannedAssignments() {
      const assignmentKeys = [];
      for (const [key, status] of this.initialAssignments.entries()) {
        if (status === 'planned') {
          assignmentKeys.push(key);
        }
      }

      if (assignmentKeys.length > 0) {
        await this.deleteAssignments(assignmentKeys);
      }

      // Clear local state
      this.assignments = [];
      this.initialAssignments = new Map();
    },
  },
})

