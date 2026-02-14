-- Create additional databases
CREATE DATABASE keycloak;
CREATE DATABASE langfuse;
-- Connect to the_expert database
\ c the_expert -- Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- Create schema if not exists (though public exists by default)
CREATE SCHEMA IF NOT EXISTS public;