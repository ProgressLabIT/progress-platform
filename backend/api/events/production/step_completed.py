from events.production.base_production import BaseProductionEvent
from events.production.batch_completed import BatchCompletedEvent
from events.serial.serial_data_updated import SerialDataUpdatedEvent
from models.event import EventInfoModel, EventType
from models.traceability import *
from utils.production import Queries as ProductionQueries


class StepCompletedEvent(BaseProductionEvent):
    class InfoModel(EventInfoModel): ...

    @classmethod
    def get_event_type(cls):
        return EventType.STEP_COMPLETED

    from events.production.commons.serial import (
        _convert_form_field,
        convert_batch_data,
        convert_form_data,
    )

    def apply(self):
        self._get_job_data()
        self.get_active_batch()

        # Save current work session and batch keys in Event.info
        self.work_session = self.get_current_work_session()
        self.info.work_session_key = self.work_session.key

        # Create StepExecutionData record
        step_data = StepExecutionData(**self.info.model_dump())
        step_data.batch_key = self.info.active_batch_key
        step_data.completed = self.info.timestamp
        step_data.status = StepStatus.DONE
        self.tx.collection("StepExecutionData").insert(step_data)

        # if last step complete batch
        if self.current_step_was_last_to_do():
            BatchCompletedEvent.create_as_child(
                self,
                dict(
                    job_key=self.info.job_key,
                    work_order_key=self.info.work_order_key,
                    phase_key=self.info.phase_key,
                    batch_serials=self.info.batch_serials,
                    completed_batch_qt=self.batch.qt_total,
                    completed_batch_key=self.batch.key,
                    product_key=self.info.product_key,
                ),
            )

        # else update job step progress
        else:
            self.update_job_step_progress()
            new_job_data = self.tx.aql.execute(
                ProductionQueries.GET_WORKING_JOB_DATA,
                bind_vars=dict(job_key=self.info.job_key),
            ).next()

            if "wo_bom" in new_job_data:
                setattr(self.job, "wo_bom", new_job_data["wo_bom"])

        self.response = dict(
            message=f"Step completed for batch {self.info.active_batch_key}",
            job_data=self.job,
            batch_data=self.get_batch_execution_data(),
        )

    def store_batch_data(self, batch_execution_data):
        if len(batch_execution_data) > 0:
            SerialDataUpdatedEvent.create_as_child(
                self,
                dict(
                    batch_key=self.info.active_batch_key,
                    batch_execution_data=batch_execution_data,
                    user_key=self.info.user_key,
                ),
            )
