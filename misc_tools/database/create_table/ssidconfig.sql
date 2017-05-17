CREATE TABLE "ssidconfig" ("id" SERIAL PRIMARY KEY, "user_id" INTEGER REFERENCES "user" (id), "name" VARCHAR(80) UNIQUE, "pass_word" VARCHAR(80), "is_activated" BOOLEAN DEFAULT TRUE);
