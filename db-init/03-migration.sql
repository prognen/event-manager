create table if not exists event_db.users_event(
    id SERIAL PRIMARY KEY,
    event_id INT NOT NULL,
    users_id INT NOT NULL,
    CONSTRAINT fk_event_id FOREIGN KEY (event_id) REFERENCES event_db.event(id) ON DELETE CASCADE,
    CONSTRAINT fk_users_id FOREIGN KEY (users_id) REFERENCES event_db.users(id) ON DELETE CASCADE
);

INSERT INTO event_db.users_event(users_id, event_id)
SELECT user_id, id
FROM event_db.event
WHERE user_id IN (SELECT id FROM event_db.users);
ALTER TABLE event_db.event DROP COLUMN user_id;
