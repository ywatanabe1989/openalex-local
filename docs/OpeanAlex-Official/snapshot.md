<!-- ---
!-- Timestamp: 2026-01-25 19:23:27
!-- Author: ywatanabe
!-- File: /ssh:nas:/home/ywatanabe/proj/openalex-local/docs/OpeanAlex-Official/snapshot.md
!-- --- -->

# OpenAlex snapshot

For most use cases, the REST API is your best option. However, you can also download ([instructions here](https://docs.openalex.org/download-all-data/download-to-your-machine)) and install a complete copy of the OpenAlex database on your own server, using the database snapshot. The snapshot consists of seven files (split into smaller files for convenience), with one file for each of our seven entity types. The files are in the [JSON Lines](https://jsonlines.org/) format; each line is a JSON object, exactly the same as [you'd get from our API](https://docs.openalex.org/api-entities/works/get-a-single-work). The properties of these JSON objects are documented in each entity's object section (for example, the [`Work`](https://docs.openalex.org/api-entities/works/work-object) object).

The snapshot is updated about once per month; you can read [release notes for each new update here.](https://github.com/ourresearch/openalex-guts/blob/main/files-for-datadumps/standard-format/RELEASE_NOTES.txt)

If you've worked with a dataset like this before, the [snapshot data format](https://docs.openalex.org/download-all-data/snapshot-data-format) may be all you need to get going. If not, read on.

The rest of this guide will tell you how to (a) download the snapshot and (b) upload it to your own database. We’ll cover two general approaches:

* Load the intact OpenAlex records to a data warehouse (we’ll use [BigQuery](https://cloud.google.com/bigquery) as an example) and use native JSON functions to query the [Work](https://docs.openalex.org/api-entities/works/work-object), [Author](https://docs.openalex.org/api-entities/authors/author-object), [Source](https://docs.openalex.org/api-entities/sources/source-object), [Institution](https://docs.openalex.org/api-entities/institutions/institution-object), [Concept](https://docs.openalex.org/api-entities/concepts/concept-object), and [Publisher](https://docs.openalex.org/api-entities/publishers/publisher-object) objects directly.
* Flatten the records into a normalized schema in a relational database (we’ll use [PostgreSQL](https://www.postgresql.org/)) while preserving the relationships between objects.

We'll assume you're initializing a fresh snapshot. To keep it up to date, you'll have to take the information from [Downloading updated Entities](https://docs.openalex.org/snapshot-data-format#downloading-updated-entities) and generalize from the steps in the guide.

{% hint style="warning" %}
This is hard. Working with such a big and complicated dataset hardly ever goes according to plan. If it gets scary, try the [REST API](https://docs.openalex.org/how-to-use-the-api/api-overview). In fact, try the REST API first. It can answer most of your questions and has a much lower barrier to entry.
{% endhint %}

There’s more than one way to do everything. We’ve tried to pick one reasonable default way to do each step, so if something doesn’t work in your environment or with the tools you have available, let us know.

Up next: the snapshot [data format](https://docs.openalex.org/download-all-data/snapshot-data-format), [downloading the data](https://docs.openalex.org/download-all-data/download-to-your-machine) and [getting it into your database](https://docs.openalex.org/download-all-data/upload-to-your-database).

# Snapshot data format

Here are the details on where the OpenAlex data lives and how it's structured.

* All the data is stored in [Amazon S3](https://aws.amazon.com/s3/), in the [`openalex`](https://openalex.s3.amazonaws.com/browse.html) bucket.
* The data files are gzip-compressed [JSON Lines](https://jsonlines.org/), one row per entity.
* The bucket contains one prefix (folder) for each entity type: [work](https://openalex.s3.amazonaws.com/browse.html#data/works/), [author](https://openalex.s3.amazonaws.com/browse.html#data/authors/), [source](https://openalex.s3.amazonaws.com/browse.html#data/sources/), [institution](https://openalex.s3.amazonaws.com/browse.html#data/institutions/), [concept](https://openalex.s3.amazonaws.com/browse.html#data/concepts/), and [publisher](https://openalex.s3.amazonaws.com/browse.html#data/publishers/).
* Records are partitioned by [updated\_date](https://docs.openalex.org/api-entities/works/work-object#updated_date). Within each entity type prefix, each object (file) is further prefixed by this date. For example, if an [`Author`](https://docs.openalex.org/api-entities/authors/author-object) has an updated\_date of 2021-12-30 it will be prefixed`/data/authors/updated_date=2021-12-30/`.
  * If you're initializing a fresh snapshot, the `updated_date` partitions aren't important yet. You need all the entities, so for `Authors` you would get [`/data/authors`](https://openalex.s3.amazonaws.com/browse.html#data/authors/)`/*/*.gz`
* There are multiple objects under each `updated_date` partition. Each is under 2GB.
* The manifest file is JSON (in [redshift manifest](https://docs.aws.amazon.com/redshift/latest/dg/loading-data-files-using-manifest.html) format) and lists all the data files for each object type - [`/data/works/manifest`](https://openalex.s3.amazonaws.com/data/works/manifest) lists all the works.
* The gzip-compressed snapshot takes up about 330 GB and decompresses to about 1.6 TB.

The structure of each entity type is documented here: [Work](https://docs.openalex.org/api-entities/works/work-object), [Author](https://docs.openalex.org/api-entities/authors/author-object), [Source](https://docs.openalex.org/api-entities/sources/source-object), [Institution](https://docs.openalex.org/api-entities/institutions/institution-object), [Concept](https://docs.openalex.org/api-entities/concepts/concept-object), and [Publisher](https://docs.openalex.org/api-entities/publishers/publisher-object).

{% hint style="info" %}
**API-only fields**: Some Work properties are only available through the API and not included in the snapshot:

* `content_url` — use the [content endpoint](https://docs.openalex.org/how-to-use-the-api/get-content) directly with work IDs from the snapshot
  {% endhint %}

{% hint style="info" %}
We have recently added folders for new entities `topics`, `fields`, `subfields`, and `domains`, and we will be adding others soon. This documentation will soon be updated to reflect these changes.
{% endhint %}

#### Visualization of the entity\_type/updated\_date folder structure

This is a screenshot showing the "leaf" nodes of one *entity type*, *updated date* folder. You can also click around the browser links above to get a sense of the snapshot's structure.

### Downloading updated Entities

Once you have a copy of the snapshot, you'll probably want to keep it up to date. The `updated_date` partitions make this easy, but the way they work may be unfamiliar. Unlike a set of dated snapshots that each contain the full dataset as of a certain date, each partition contains the records that last changed on that date.

If we imagine launching OpenAlex on 2021-12-30 with 1000 `Authors`, each being newly created on that date, `/data/authors/` looks like this:

```
/data/authors/
├── manifest
└── updated_date=2021-12-30 [1000 Authors]
    ├── 0000_part_00.gz
    ...
    └── 0031_part_00.gz
```

If, on 2022-01-04, we made changes to 50 of those `Authors`, they would come *out of* one of the files in `/data/authors/updated_date=2021-12-30` and go *into* one in `/data/authors/updated_date=2022-01-04:`

```
/data/authors/
├── manifest
├── updated_date=2021-12-30 [950 Authors]
│   ├── 0000_part_00.gz
│   ...
│   └── 0031_part_00.gz
└── updated_date=2022-01-04 [50 Authors]
    ├── 0000_part_00.gz
    ...
    └── 0031_part_00.gz
```

If we also discovered 50 *new* Authors, they would go in that same partition, so the totals would look like this:

```
/data/authors/
├── manifest
├── updated_date=2021-12-30 [950 Authors]
│   ├── 0000_part_00.gz
│   ...
│   └── 0031_part_00.gz
└── updated_date=2022-01-04 [100 Authors]
    ├── 0000_part_00.gz
    ...
    └── 0031_part_00.gz
```

So if you made your copy of the snapshot on 2021-12-30, you would only need to download `/data/authors/updated_date=2022-01-04` to get everything that was changed or added since then.

{% hint style="info" %}
To update a snapshot copy that you created or updated on date `X`, insert or update the records in objects where `updated_date` > `X`*.*
{% endhint %}

You never need to go back for a partition you've already downloaded. Anything that changed isn't there anymore, it's in a new partition.

At the time of writing, these are the `Author` partitions and the number of records in each (in the actual dataset):

* `updated_date=2021-12-30/` - 62,573,099
* `updated_date=2022-12-31/` - 97,559,192
* `updated_date=2022-01-01/` - 46,766,699
* `updated_date=2022-01-02/` - 1,352,773

This reflects the creation of the dataset on 2021-12-30 and 145,678,664 combined updates and inserts since then - 1,352,773 of which were on 2022-01-02. Over time, the number of partitions will grow. If we make a change that affects all records, the partitions before the date of the change will disappear.

### Merged Entities

{% hint style="info" %}
See [Merged Entities](https://docs.openalex.org/how-to-use-the-api/get-single-entities#merged-entity-ids) for an explanation of what Entity merging is and why we do it.
{% endhint %}

Alongside the folders for the six Entity types - work, author, source, institution, concept, and publisher - you'll find a seventh folder: [merged\_ids](https://openalex.s3.amazonaws.com/browse.html#data/merged_ids/). Within this folder you'll find the IDs of Entities that have been merged away, along with the Entity IDs they were merged into.

Keep in mind that merging an Entity ID is a way of deleting the Entity while persisting its ID in OpenAlex. In practice, you can just delete the Entity it belongs to. It's not necessary to keep track of the date or which entity it was merged into.

Merge operations are separated into files by date. Each file lists the IDs of Entities that were merged on that date, and names the Entities they were merged into.

```
/data/merged_ids/
├── authors
│   └── 2022-06-07.csv.gz
├── institutions
│   └── 2022-06-01.csv.gz
├── venues
│   └── 2022-06-03.csv.gz
└── works
    └── 2022-06-06.csv.gz
```

For example, `data/merged_ids/authors/2022-06-07.csv.gz` begins:

```
merge_date,id,merge_into_id
2022-06-07,A2257618939,A2208157607
```

When processing this file, all you need to do is delete A2257618939. The effects of merging these authors, like crediting A2208157607 with their Works, are already reflected in the affected Entities.

Like the Entities' *updated\_date* partitions, you only ever need to download merged\_ids files that are new to you. Any later merges will appear in new files with later dates.

### The `manifest` file

When we start writing a new `updated_date` partition for an entity, we'll delete that entity's `manifest` file. When we finish writing the partition, we'll recreate the manifest, including the newly-created objects. So if `manifest` is there, all the entities are there too.

The file is in [redshift manifest](https://docs.aws.amazon.com/redshift/latest/dg/loading-data-files-using-manifest.html) format. To use it as part of the update process for an Entity type (we'll keep using Authors as an example):

1. Download [`s3://openalex/data/authors/manifest`](https://openalex.s3.amazonaws.com/data/authors/manifest)`.`
2. Get the file list from the `url` property of each item in the `entries` list.
3. Download any objects with an `updated_date` you haven't seen before.
4. Download [`s3://openalex/data/authors/manifest`](https://openalex.s3.amazonaws.com/data/authors/manifest) again. If it hasn't changed since (1), no records moved around and any date partitions you downloaded are valid.
5. Decompress the files you downloaded and parse one JSON `Author` per line. Insert or update into your database of choice, using [each entity's ID](https://docs.openalex.org/how-to-use-the-api/get-single-entities#the-openalex-id) as a primary key.

If you’ve worked with dataset like this before and have a toolchain picked out, this may be all you need to know. If you want more detailed steps, proceed to [download the data](https://docs.openalex.org/download-all-data/download-to-your-machine).


# Download to your machine

First off: anyone can get the data for free. While the files are hosted on [S3](https://aws.amazon.com/s3/) and we’ll be using Amazon tools in these instructions, you don’t need an Amazon account.

{% hint style="info" %}
Many thanks to the [AWS Open Data program](https://aws.amazon.com/opendata/). They cover the data-transfer fees (about $70 per download!) so users don't have to.
{% endhint %}

Before you load the snapshot contents to your database, you’ll need to get the files that make it up onto your own computer. There are exceptions, like [loading to redshift from s3](https://docs.aws.amazon.com/redshift/latest/dg/tutorial-loading-data.html) or using an ETL product like [Xplenty](https://xplenty.com) with an S3 connector. If either of these apply to you, see if the [snapshot data format](https://docs.openalex.org/download-all-data/snapshot-data-format) is enough to get you started.

The easiest way to get the files is with the Amazon Web Services Command Line Interface (AWS CLI). Sample commands in this documentation will use the AWS CLI. You can find instructions for installing it on your system here: <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>

You can also browse the snapshot files using the AWS console here: <https://openalex.s3.amazonaws.com/browse.html>. This browser and the CLI will work without an account.

This shell command will copy everything in the `openalex` S3 bucket to a local folder named `openalex-snapshot`. It'll take up roughly 300GB of disk space.

```bash
aws s3 sync "s3://openalex" "openalex-snapshot" --no-sign-request
```

{% hint style="warning" %}
If you download the snapshot into an existing folder, you'll need to use the [`aws s3 sync`](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html) `--delete` flag to remove files from any previous downloads. You can also remove the contents of destination folder manually. If you don't, you will see duplicate Entities that have moved from one file to another between snapshot updates.
{% endhint %}

The size of the snapshot will change over time. You can check the current size before downloading by looking at the output of:

```bash
aws s3 ls --summarize --human-readable --no-sign-request --recursive "s3://openalex/"
```

You should get a file structure like this (edited for length - there are more objects in the actual bucket):

```
openalex-snapshot/
├── LICENSE.txt
├── RELEASE_NOTES.txt
└── data
    ├── authors
    │   ├── manifest
    │   └── updated_date=2021-12-28
    │       ├── 0000_part_00.gz
    │       └── 0001_part_00.gz
    ├── concepts
    │   ├── manifest
    │   └── updated_date=2021-12-28
    │       ├── 0000_part_00.gz
    │       └── 0001_part_00.gz
    ├── institutions
    │   ├── manifest
    │   └── updated_date=2021-12-28
    │       ├── 0000_part_00.gz
    │       └── 0001_part_00.gz
    ├── sources
    │   ├── manifest
    │   └── updated_date=2021-12-28
    │       ├── 0000_part_00.gz
    │       └── 0001_part_00.gz
    └── works
        ├── manifest
        └── updated_date=2021-12-28
            ├── 0000_part_00.gz
            └── 0001_part_00.gz
```

# Upload to your database

Now that you have a copy of the OpenAlex data you can do one these:

* upload it to a [data warehouse](https://docs.openalex.org/download-all-data/upload-to-your-database/load-to-a-data-warehouse)
* upload it to a [relational database](https://docs.openalex.org/download-all-data/upload-to-your-database/load-to-a-relational-database)

# Load to a data warehouse

In many data warehouse and document store applications, you can load the OpenAlex entities as-is and query them directly. We’ll use [BigQuery](https://cloud.google.com/bigquery) as an example here. ([Elasticsearch](https://www.elastic.co/elasticsearch/) docs coming soon). To follow along you’ll need the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install). You’ll also need a Google account that can make BigQuery tables that are, well… big. Which means it probably won’t be free.

We'll show you how to do this in 4 steps:

1. Create a BigQuery Project and Dataset to hold your tables
2. Create the tables that will hold your entity JSON records
3. Copy the data files to the tables you created
4. Run some queries on the data you loaded

{% hint style="info" %}
Several users have contributed more self-contained scripts for this. We haven't tested these but they may be easier options:\
\* <https://github.com/naustica/openalex>\
\* <https://github.com/DrorSh/openalex_to_gbq>
{% endhint %}

{% hint style="info" %}
[Snowflake](https://www.snowflake.com/) users can connect to a ready-to-query data set on the marketplace, helpfully maintained by [Util](https://www.util.co/) - <https://app.snowflake.com/marketplace/listing/GZT0ZOMX4O7>
{% endhint %}

## **Step 1: Create a BigQuery Project and Dataset**

In BigQuery, you need a [Project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) and [Dataset](https://cloud.google.com/bigquery/docs/datasets-intro) to hold your tables. We’ll call the project “openalex-demo” and the dataset “openalex”. Follow the linked instructions to create the Project, then create the dataset inside it:

```bash
bq mk openalex-demo:openalex
```

> `Dataset 'openalex-demo:openalex' successfully created`

## Step 2: Create tables for each entity type

Now, we’ll [create tables](https://cloud.google.com/bigquery/docs/tables) inside the dataset. There will be 5 tables, one for each entity type. Since we’re using JSON, each table will have just one text column named after the table.

```bash
bq mk --table openalex-demo:openalex.works work:string
```

> `Table 'openalex-demo:openalex.works' successfully created.`

```bash
bq mk --table openalex-demo:openalex.authors author:string
```

> `Table 'openalex-demo:openalex.authors' successfully created`

and so on for `sources`, `institutions`, `concepts,` and `publishers`.

## Step 3: Load the data files

We’ll load each table’s data from the JSON Lines files we downloaded earlier. For `works`, the files were:

* openalex-snapshot/data/works/updated\_date=2021-12-28/0000\_part\_00.gz
* openalex-snapshot/data/works/updated\_date=2021-12-28/0001\_part\_00.gz

Here’s a command to load one `works` file (don’t run it yet):

```bash
bq load \
--project_id openalex-demo \
--source_format=CSV -F '\t' \
--schema 'work:string' \
openalex.works \
'openalex-snapshot/data/works/updated_date=2021-12-28/0000_part_00.gz'
```

{% hint style="info" %}
See the full documentation for the `bq load` command here: <https://cloud.google.com/bigquery/docs/reference/bq-cli-reference#bq_load>
{% endhint %}

This part of the command may need some explanation:

> `--source_format=CSV -F '\t' --schema 'work:string'`

Bigquery is expecting multiple columns with predefined datatypes (a “schema”). We’re tricking it into accepting a single text column (`--schema 'work:string'`) by specifying [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) format (`--source_format=CSV`) with a column delimiter that isn’t present in the file (`-F '\t')` (\t means “tab”).

`bq load` can only handle one file at a time, so you must run this command once per file. But remember that the real dataset will have many more files than this example does, so it's impractical to copy, edit, and rerun the command each time. It's easier to handle all the files in a loop, like this:

```bash
for data_file in openalex-snapshot/data/works/*/*.gz;
do
    bq load --source_format=CSV -F '\t' \
        --schema 'work:string' \
        --project_id openalex-demo \
        openalex.works $data_file;
done
```

{% hint style="info" %}
This step is slow. *How* slow depends on your upload speed, but for `Author` and `Work` we're talking hours, not minutes.

You can speed this up by using [`parallel`](https://www.gnu.org/software/parallel/) or other tools to run multiple upload commands at once. If you do, watch out for errors caused by hitting [BigQuery quota](https://cloud.google.com/bigquery/docs/troubleshoot-quotas) limits.
{% endhint %}

Do this once per entity type, substituting each entity name for `work`/`works` as needed. When you’re finished, you’ll have five tables that look like this:

## **Step 4: Run your queries!**

Now you have the all the OpenAlex data in a place where you can do anything you want with it using [BigQuery JSON functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/json_functions) through [bq query](https://cloud.google.com/bigquery/docs/reference/bq-cli-reference#bq_query) or the BigQuery [console](https://console.cloud.google.com/bigquery).

Here’s a simple one, extracting the OpenAlex ID and OA status for each work:

```sql
select 
    json_value(work, '$.id') as work_id, 
    json_value(work, '$.open_access.is_oa') as is_oa
from
    `openalex-demo.openalex.works`;
```

It will give you a list of IDs (this is a truncated sample, the real result will be millions of rows):

|                                    |       |
| ---------------------------------- | ----- |
| <https://openalex.org/W2741809807> | TRUE  |
| <https://openalex.org/W1491283979> | FALSE |
| <https://openalex.org/W1491315632> | FALSE |

You can run queries like this directly in your shell:

```bash
bq query \
--project_id=openalex-demo \
--use_legacy_sql=false \
"select json_value(work, '$.id') as work_id, json_value(work, '$.open_access.is_oa') as is_oa from openalex.works;"
```

But even simple queries are hard to read and edit this way. It’s better to write them in a file than directly on the command line. Here’s an example of a slightly more complex query - finding the author with the most open access works of all time:

```sql
with work_authorships_oa as (
   select
       json_value(work, '$.id') as work_id,
       json_query_array(work, '$.authorships') as authorships,
       cast(json_value(work, '$.open_access.is_oa') as BOOL) as is_oa
   from `openalex-demo.openalex.works`
), flat_authorships as (
   select work_id, authorship, is_oa
   from work_authorships_oa,
   unnest(authorships) as authorship
)
select 
    json_value(authorship, '$.author.id') as author_id,
    count(distinct work_id) as num_oa_works
from flat_authorships
where is_oa
group by author_id
order by num_oa_works desc
limit 1;
```

We get one result:

| author\_id                         | num\_oa\_works |
| ---------------------------------- | -------------- |
| <https://openalex.org/A2798520857> | 3297           |

Checking out <https://api.openalex.org/authors/A2798520857>, we see that this is Ashok Kumar at Manipal University Jaipur.

# Load to a relational database

Compared to using a data warehouse, loading the dataset into a relational database takes more work up front but lets you write simpler queries and run them on less powerful machines. One important caveat is that this is a *lot* of data, and exploration will be very slow in most relational databases.

{% hint style="info" %}
By using a relational database, you trade flexibility for efficiency in certain selected operations. The tables, columns, and indexes we have chosen in this guide represent only one of many ways the entity objects could be stored. It may not be the best way to store them given the queries you want to run. Some queries will be fast, others will be painfully slow.
{% endhint %}

We’re going to use [PostgreSQL](https://www.postgresql.org/) as an example and skip the database server setup itself. We’ll assume you have a working postgres 13+ installation on which you can create schemas and tables and run queries. With that as a starting point, we'll take you through these steps:

1. Define the tables the data will be stored in and some key relationships between them (the "schema").
2. Convert the [JSON Lines](https://jsonlines.org/) files you [downloaded](https://docs.openalex.org/download-all-data/download-to-your-machine) to [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) files that can be read by the database application. We'll flatten them to fit a [hierarchical database model](https://en.wikipedia.org/wiki/Hierarchical_database_model).
3. Load the CSV data into to the tables you created.
4. Run some queries on the data you loaded.

## Step 1: Create the schema

Running [this SQL](https://github.com/ourresearch/openalex-documentation-scripts/blob/main/openalex-pg-schema.sql) on your database (in the [psql](https://www.postgresql.org/docs/13/app-psql.html) client, for example) will initialize a schema for you.

Run it and you'll be set up to follow the next steps. To show you what it's doing, we'll explain some excerpts here, using the [concept](https://docs.openalex.org/api-entities/concepts) entity as an example.

{% hint style="warning" %}
SQL in this section isn't anything additional you need to run. It's part of the schema we already defined in the file above.
{% endhint %}

The key thing we're doing is "flattening" the nested JSON data. Some parts of this are easy. [Concept.id](https://docs.openalex.org/api-entities/concepts/concept-object#id) is just a string, so it goes in a text column called "id":

```sql
CREATE TABLE openalex.concepts (
    id text NOT NULL,
    -- plus some other columns ...
);
```

But [Concept.related\_concepts](https://docs.openalex.org/api-entities/concepts/concept-object#related_concepts) isn't so simple. You could store the JSON array intact in a postgres [JSON or JSONB](https://www.postgresql.org/docs/9.4/datatype-json.html) column, but you would lose much of the benefit of a relational database. It would be hard to answer questions about related concepts with more than one degree of separation, for example. So we make a separate table to hold these relationships:

```sql
CREATE TABLE openalex.concepts_related_concepts (
    concept_id text,
    related_concept_id text,
    score real
);
```

We can preserve `score` in this relationship table and look up any other attributes of the [dehydrated related concepts](https://docs.openalex.org/api-entities/concepts/concept-object#the-dehydratedconcept-object) in the main table `concepts`. Creating indexes on `concept_id` and `related_concept_id` lets us look up concepts on both sides of the relationship quickly.

## Step 2: Convert the JSON Lines files to CSV

[This python script](https://github.com/ourresearch/openalex-documentation-scripts/blob/main/flatten-openalex-jsonl.py) will turn the JSON Lines files you downloaded into CSV files that can be copied to the the tables you created in step 1.

{% hint style="warning" %}
This script assumes your downloaded snapshot is in `openalex-snapshot` and you've made a directory `csv-files` to hold the CSV files.

Edit `SNAPSHOT_DIR` and `CSV_DIR` at the top of the script to read or write the files somewhere else.
{% endhint %}

{% hint style="info" %}
This script has only been tested using python 3.9.5.
{% endhint %}

Copy the script to the directory above your snapshot (if the snapshot is in `/home/yourname/openalex/openalex-snapshot/`, name it something like `/home/yourname/openalex/flatten-openalex-jsonl.py)`

run it like this:

```bash
mkdir -p csv-files
python3 flatten-openalex-jsonl.py
```

{% hint style="info" %}
This script is slow. Exactly how slow depends on the machine you run it on, but think hours, not minutes.

If you're familiar with python, there are two big improvements you can make:

* Run [`flatten_authors`](https://github.com/ourresearch/openalex-documentation-scripts/blob/main/flatten-openalex-jsonl.py#L214) and [`flatten_works`](https://github.com/ourresearch/openalex-documentation-scripts/blob/main/flatten-openalex-jsonl.py#L544) at the same time, either by using threading in python or just running two copies of the script with the appropriate lines commented out.
* Flatten multiple `.gz` files within each entity type at the same time. This means parallelizing the `for jsonl_file_name ... loop` in each `flatten_` function and writing multiple CSV files per entity type.
  {% endhint %}

You should now have a directory full of nice, flat CSV files:

```
$ tree csv-files/
csv-files/
├── concepts.csv
├── concepts_ancestors.csv
├── concepts_counts_by_year.csv
├── concepts_ids.csv
└── concepts_related_concepts.csv
...
$ cat csv-files/concepts_related_concepts.csv
concept_id,related_concept_id,score
https://openalex.org/C41008148,https://openalex.org/C33923547,253.92
https://openalex.org/C41008148,https://openalex.org/C119599485,153.019
https://openalex.org/C41008148,https://openalex.org/C121332964,143.935
...
```

## Step 3: Load the CSV files to the database

Now we run one postgres copy command to load each CSV file to its corresponding table. Each command looks like this:

```
\copy openalex.concepts_ancestors (concept_id, ancestor_id) from csv-files/concepts_ancestors.csv csv header
```

[This script](https://github.com/ourresearch/openalex-documentation-scripts/blob/main/copy-openalex-csv.sql) will run all the copy commands in the right order. Here's how to run it:

1. Copy it to the same place as the python script from step 2, right above the folder with your CSV files.
2. Set the environment variable OPENALEX\_SNAPSHOT\_DB to the [connection URI](https://www.postgresql.org/docs/13/libpq-connect.html#LIBPQ-CONNSTRING) for your database.
3. If your CSV files aren't in `csv-files`, replace each occurence of 'csv-files/' in the script with the correct path.
4. Run it like this (from your shell prompt)

```bash
psql $OPENALEX_SNAPSHOT_DB < copy-openalex-csv.sql
```

or like this (from psql)

```
\i copy-openalex-csv.sql
```

There are a bunch of ways you can do this - just run the copy commands from the script above in the right order in whatever client you're familiar with.

## Step 4: Run your queries!

Now you have all the OpenAlex data in your database and can run queries in your favorite client.

Here’s a simple one, getting the OpenAlex ID and OA status for each work:

```sql
select w.id, oa.oa_status
from openalex.works w 
join openalex.works_open_access oa 
on w.id = oa.work_id;
```

You'll get results like this (truncated, the actual result will be millions of rows):

| id                                 | oa\_status |
| ---------------------------------- | ---------- |
| <https://openalex.org/W1496190310> | closed     |
| <https://openalex.org/W2741809807> | gold       |
| <https://openalex.org/W1496404095> | bronze     |

Here’s an example of a more complex query - finding the author with the most open access works of all time:

```sql
select 
    author_id, 
    count(distinct work_id) as num_oa_works 
from (
    select 
        a.id as author_id, 
        w.id as work_id, 
        oa.is_oa  
    from 
        openalex.authors a 
        join openalex.works_authorships wa on a.id = wa.author_id 
        join openalex.works w on wa.work_id = w.id 
        join openalex.works_open_access oa on w.id = oa.work_id
) work_authorships_oa 
where is_oa 
group by 1 
order by 2 desc 
limit 1;
```

We get the one row we asked for:

| author\_id                         | num\_oa\_works |
| ---------------------------------- | -------------- |
| <https://openalex.org/A2798520857> | 3297           |

Checking out <https://api.openalex.org/authors/A2798520857>, we see that this is Ashok Kumar at Manipal University Jaipur. We could also have found this directly in the query, through `openalex.authors`.

<!-- EOF -->