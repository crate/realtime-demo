CREATE TABLE IF NOT EXISTS "doc"."payments" (
   "ts" TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
   "customer_id" TEXT NOT NULL,
   "category" TEXT NOT NULL,
   "age_category" INTEGER,
   "amount" DOUBLE PRECISION NOT NULL,
   "ts_day" TIMESTAMP WITHOUT TIME ZONE GENERATED ALWAYS AS DATE_TRUNC('day', "ts")
)
CLUSTERED INTO 4 SHARDS
PARTITIONED BY ("ts_day");

CREATE TABLE IF NOT EXISTS "doc"."age_categories" (
   "category_id" INTEGER,
   "description" TEXT
);

INSERT INTO "doc"."age_categories" VALUES (3, '36 - 45'), (4, '46 - 55'), (5, '56 - 65'), (2, '26 - 35'), (0, '<= 18'), (1, '19 - 25'), (6, '> 65');