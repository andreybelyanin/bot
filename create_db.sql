create table if not exists clients(
    id integer primary key,
    name varchar(255),
    description text,
    created datetime
);

create table if not exists appointment(
    id integer primary key,
    appointment_date datetime,
    description text,
    price integer,
    client_id integer,
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
);

create table if not exists notes(
    note_date datetime,
    note text
);