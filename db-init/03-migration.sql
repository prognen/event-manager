create table if not exists travel_db.users_travel(
    id SERIAL PRIMARY KEY,
    travel_id INT NOT NULL,
    users_id INT NOT NULL,
    CONSTRAINT fk_travel_id FOREIGN KEY (travel_id) REFERENCES travel_db.travel(id) ON DELETE CASCADE,
    CONSTRAINT fk_users_id FOREIGN KEY (users_id) REFERENCES travel_db.users(id) ON DELETE CASCADE
);

INSERT INTO travel_db.users_travel(users_id, travel_id)
SELECT user_id, id
FROM travel_db.travel
WHERE user_id IN (SELECT id FROM travel_db.users);
ALTER TABLE travel_db.travel DROP COLUMN user_id;