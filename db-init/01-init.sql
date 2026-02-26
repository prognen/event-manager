create schema if not exists event_db;
CREATE TABLE if not exists event_db.venue (
    venue_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS event_db.program (
    id SERIAL PRIMARY KEY,
    type_transport VARCHAR(100) NOT NULL,
    from_venue INT NOT NULL,
    to_venue INT NOT NULL,
    distance INT NOT NULL,
    cost INT NOT NULL,
    CONSTRAINT fk_from_venue FOREIGN KEY (from_venue) REFERENCES event_db.venue(venue_id) ON DELETE CASCADE,
    CONSTRAINT fk_to_venue FOREIGN KEY (to_venue) REFERENCES event_db.venue(venue_id) ON DELETE CASCADE
);

CREATE TABLE if not exists event_db.users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    passport VARCHAR(20) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    login VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT null,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE 
);

CREATE TABLE if not exists event_db.activity (
    id SERIAL PRIMARY KEY,
    duration VARCHAR(50) NOT NULL,
    address VARCHAR(255) NOT NULL,
    activity_type VARCHAR(255) NOT NULL,
    activity_time TIMESTAMP NOT NULL,
    venue INT NOT NULL,
    CONSTRAINT fk_venue FOREIGN KEY (venue) REFERENCES event_db.venue(venue_id) ON DELETE CASCADE
);

CREATE TABLE if not exists event_db.lodgings (
    id SERIAL PRIMARY KEY,
    price INT NOT NULL,
    address VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    rating INT NOT NULL,
    check_in TIMESTAMP NOT NULL,
    check_out TIMESTAMP NOT NULL,
    venue INT NOT NULL,
    CONSTRAINT fk_venue FOREIGN KEY (venue) REFERENCES event_db.venue(venue_id) ON DELETE CASCADE
);

create table if not exists event_db.event (
	id SERIAL PRIMARY KEY,
	status VARCHAR(50) not null,
	user_id int not null,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES event_db.users(id) ON DELETE CASCADE 
);

create table if not exists event_db.session (
	id SERIAL PRIMARY KEY,
	program_id INT not null,
	event_id INT not null,
	start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT null,
    type VARCHAR(20) NOT null,
    CONSTRAINT fk_program_id FOREIGN KEY (program_id) REFERENCES event_db.program(id) ON DELETE CASCADE,
    CONSTRAINT fk_event_id FOREIGN KEY (event_id) REFERENCES event_db.event(id) ON DELETE CASCADE
);


create table if not exists event_db.event_activity (
	id SERIAL PRIMARY KEY,
	event_id INT not null,
	activity_id int not null,
    CONSTRAINT fk_event_id FOREIGN KEY (event_id) REFERENCES event_db.event(id) ON DELETE CASCADE,
    CONSTRAINT fk_activity_id FOREIGN KEY (activity_id) REFERENCES event_db.activity(id) ON DELETE CASCADE
);

create table if not exists event_db.event_lodgings (
	id SERIAL PRIMARY KEY,
	event_id INT not null,
	lodging_id int not null,
    CONSTRAINT fk_event_id FOREIGN KEY (event_id) REFERENCES event_db.event(id) ON DELETE CASCADE,
    CONSTRAINT fk_lodging_id FOREIGN KEY (lodging_id) REFERENCES event_db.lodgings(id) ON DELETE CASCADE
);

create table if not exists event_db.users_event(
    id SERIAL PRIMARY KEY,
    event_id INT NOT NULL,
    users_id INT NOT NULL,
    CONSTRAINT fk_event_id FOREIGN KEY (event_id) REFERENCES event_db.event(id) ON DELETE CASCADE,
    CONSTRAINT fk_users_id FOREIGN KEY (users_id) REFERENCES event_db.users(id) ON DELETE CASCADE
)
