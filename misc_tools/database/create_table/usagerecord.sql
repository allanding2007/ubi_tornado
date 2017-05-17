CREATE TABLE "usagerecord" ("id" SERIAL PRIMARY KEY, "device_id" INTEGER REFERENCES "device" (id), "data_usage" FLOAT, "cost" BOOLEAN DEFAULT TRUE, "begin_date" TIMESTAMP, "end_date" TIMESTAMP);
