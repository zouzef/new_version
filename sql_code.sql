
DELIMITER $$

CREATE TRIGGER trg_after_update
AFTER UPDATE ON attendance
FOR EACH ROW
BEGIN
    -- Only insert if slc_edit = 1 AND something actually changed
    IF NEW.slc_edit = 1 AND
       JSON_OBJECT(
           'attendanceID', OLD.id,
           'userID', OLD.user_id,
           'calander_id', OLD.calander_id,
           'is_present', OLD.is_present,
           'note', OLD.note
           'enabled',OLD.enabled
       ) <> JSON_OBJECT(
           'attendanceID', NEW.id,
           'userID', NEW.user_id,
           'calander_id', NEW.calander_id,
           'is_present', NEW.is_present,
           'note', NEW.note
           'enabled',NEW.enabled
       )
    THEN
        INSERT INTO attendance_audit
        (
            action_type,
            old_data,
            new_data,
            changed_at,
            is_synced,
            id_attendance
        ) VALUES
        (
            'UPDATE',
            JSON_OBJECT(
                'attendanceID', OLD.id,
                'userID', OLD.user_id,
                'calander_id', OLD.calander_id,
                'is_present', OLD.is_present,
                'note', OLD.note,
                'enabled',OLD.enabled
            ),
            JSON_OBJECT(
                'attendanceID', NEW.id,
                'userID', NEW.user_id,
                'calander_id', NEW.calander_id,
                'is_present', NEW.is_present,
                'note', NEW.note,
                'enabled',NEW.enabled
            ),
            NOW(),
            0,
            NEW.id
        );
    END IF;
END$$

DELIMITER ;


DELIMITER $$
CREATE TRIGGER trg_after_delete
AFTER