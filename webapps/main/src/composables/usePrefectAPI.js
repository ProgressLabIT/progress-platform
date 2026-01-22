/**
 * Composable for interacting with Prefect API to monitor workflows.
 * 
 * This composable provides functions to:
 * - Find Prefect deployments by name
 * - Get flow runs for a deployment
 * - Find flow runs by session parameter
 * - Trigger new flow runs
 * 
 * @module usePrefectAPI
 */

import axios from 'axios'

export function usePrefectAPI() {
  const prefectBaseUrl = window.location.protocol + '//' + 
    window.location.hostname + ':4200/api'

  /**
   * Find a deployment by name pattern
   * @param {string} deploymentName - Name pattern to search for (supports SQL LIKE)
   * @returns {Promise<Object|null>} Deployment object or null if not found
   */
  async function findDeploymentByName(deploymentName) {
    try {
      const response = await axios.post(`${prefectBaseUrl}/deployments/filter`, {
        deployments: { name: { like_: deploymentName } },
        limit: 1
      })
      return response.data[0] || null
    } catch (error) {
      console.error('Error finding deployment:', error)
      throw error
    }
  }

  /**
   * Get flow runs for a specific deployment
   * @param {string} deploymentId - The deployment ID
   * @param {number} limit - Maximum number of runs to return (default: 1)
   * @returns {Promise<Array>} Array of flow run objects
   */
  async function getFlowRunsByDeployment(deploymentId, limit = 1) {
    try {
      const response = await axios.post(`${prefectBaseUrl}/flow_runs/filter`, {
        flow_runs: { deployment_id: { any_: [deploymentId] } },
        sort: 'START_TIME_DESC',
        limit
      })
      return response.data || []
    } catch (error) {
      console.error('Error fetching flow runs:', error)
      throw error
    }
  }

  /**
   * Find the flow run for a specific count session
   * @param {string} sessionKey - The count session key
   * @returns {Promise<Object|null>} Flow run object or null if not found
   */
  async function getFlowRunsForSession(sessionKey) {
    try {
      // Find deployment
      const deployment = await findDeploymentByName('apply_inventory_counts')
      if (!deployment) {
        console.warn('Deployment "apply_inventory_counts" not found')
        return null
      }

      // Get recent flow runs for this deployment
      const flowRuns = await getFlowRunsByDeployment(deployment.id, 10)
      
      // Find the flow run with matching session_key parameter
      const matchingRun = flowRuns.find(run => 
        run.parameters?.session_key === sessionKey
      )

      return matchingRun || null
    } catch (error) {
      console.error('Error getting flow runs for session:', error)
      throw error
    }
  }

  /**
   * Trigger a new flow run for a deployment
   * @param {string} deploymentId - The deployment ID
   * @param {Object} parameters - Flow run parameters
   * @returns {Promise<Object>} Created flow run object
   */
  async function triggerFlowRun(deploymentId, parameters) {
    try {
      const response = await axios.post(
        `${prefectBaseUrl}/deployments/${deploymentId}/create_flow_run`,
        {
          state: { type: 'SCHEDULED' },
          parameters
        }
      )
      return response.data
    } catch (error) {
      console.error('Error triggering flow run:', error)
      throw error
    }
  }

  return {
    findDeploymentByName,
    getFlowRunsByDeployment,
    getFlowRunsForSession,
    triggerFlowRun
  }
}
