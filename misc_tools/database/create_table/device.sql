CREATE TABLE "device" ("id" SERIAL PRIMARY KEY, "user_id" INTEGER REFERENCES "user" (id), "mac_address" VARCHAR(80) UNIQUE, "manuf" VARCHAR(80), "description" VARCHAR(120), "is_activated" BOOLEAN DEFAULT TRUE, "join_date" TIMESTAMP);
