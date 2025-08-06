-- PostgreSQL initialization script for Handle.Net server
-- This script creates the necessary tables for Handle.Net SQL storage

-- Create nas table (Naming Authority records) - following Handle.Net Manual section 8.2
CREATE TABLE nas (
    na BYTEA NOT NULL,
    PRIMARY KEY (na)
);

-- Create handles table - following Handle.Net Manual section 8.2 exact schema
CREATE TABLE handles (
    handle BYTEA NOT NULL,
    idx INT4 NOT NULL,
    type BYTEA,
    data BYTEA,
    ttl_type INT2,
    ttl INT4,
    timestamp INT4,
    refs TEXT,
    admin_read BOOL,
    admin_write BOOL,
    pub_read BOOL,
    pub_write BOOL,
    PRIMARY KEY (handle, idx)
);

-- Create indexes for better performance
CREATE INDEX dataindex ON handles(data);
CREATE INDEX handleindex ON handles(handle);

-- Grant privileges to the handle user
GRANT ALL PRIVILEGES ON TABLE handles TO handleuser;
GRANT ALL PRIVILEGES ON TABLE nas TO handleuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO handleuser;

-- Initialize TEST namespace and admin handle (matching MySQL approach)
INSERT INTO nas (na) VALUES ('TEST'::bytea);
INSERT INTO nas (na) VALUES ('0.NA/TEST'::bytea);

-- Create TEST/ADMIN handle with required admin credentials (matching MySQL working values)
INSERT INTO handles (handle, idx, type, data, ttl_type, ttl, timestamp,
                     admin_read, admin_write, pub_read, pub_write)
VALUES ('TEST/ADMIN'::bytea, 100, 'HS_ADMIN'::bytea,
        '\xc200000a544553542f41444d494e000000c2'::bytea,
        0, 86400,
        EXTRACT(epoch FROM now())::integer,
        true, true, true, false);

INSERT INTO handles (handle, idx, type, data, ttl_type, ttl, timestamp,
                     admin_read, admin_write, pub_read, pub_write)
VALUES ('TEST/ADMIN'::bytea, 300, 'HS_SECKEY'::bytea,
        'ASECRETKEY'::bytea,
        0, 86400,
        EXTRACT(epoch FROM now())::integer,
        true, true, false, false);
