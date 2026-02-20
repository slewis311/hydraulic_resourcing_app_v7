create table if not exists team_members (
  member text primary key,
  daily_hours double precision not null
);

create table if not exists jobs (
  job_name text not null,
  assignee text not null,
  required_hours double precision not null,
  priority integer not null,
  due_date date,
  notes text,
  primary key (job_name, assignee)
);

create table if not exists staff_settings (
  member text primary key,
  start_date date,
  working_weekdays jsonb
);

create table if not exists leave_days (
  member text not null,
  leave_date date not null,
  primary key (member, leave_date)
);
