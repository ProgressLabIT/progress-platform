# ==========================
# HOME SCREEN
# ==========================

## >>>>>>>>> MODIFY assignment data accoding to final schema
get_jobs_for_user = """

	// Get jobs assigned directly to user
	LET user_jobs = (
	    // Traverse assignments graph
	    FOR j,a IN 1..1 INBOUND @user assigned_to 
	        // filter non-job assignments (Department, etc.)
	        FILTER j._id LIKE "Job%" 
	        // Get jobs in order according to queue
	        SORT a._key 
	        RETURN {job: j, assignment: a})

	// Same thing for jobs assigned to the user's department
	LET dep_jobs = (FOR j,a IN 2..2 ANY @user assigned_to FILTER j._id LIKE "Job%" SORT a._key RETURN {job: j, assignment: a})

	RETURN { assigned_to_user: user_jobs, assigned_to_dep: dep_jobs }

"""

# >>>>> TO BE TESTED
get_ongoing_job_for_user = """

	// Starting from work session
	LET last_job = LAST(
		FOR ws in WorkSession
			FILTER ws.user === @user
			SORT ws.end
			RETURN ws._to
		)
	
	FOR j in Job
		FILTER j._id == last_job AND j.status == 'started'
		
	RETURN j

"""



# ==========================
# JOB SCREEN
# ==========================

get_job_data = """

	