# Database Design

## Database

**Database name:** `gym_data`  
**Storage engine:** InnoDB  
**Character set:** `utf8mb4`

## Tables and relationships

| Table | Purpose | Primary key | Foreign key |
|---|---|---|---|
| `members` | Stores each member's core details and service indicators. | `member_id` | None |
| `member_days` | Stores the gym days selected by each member. | `day_id` | `member_id` references `members.member_id` |
| `member_favorite_lessons` | Stores a member's favourite group lessons. | `lesson_id` | `member_id` references `members.member_id` |
| `member_favorite_drinks` | Stores a member's favourite drinks. | `drink_id` | `member_id` references `members.member_id` |

## Relationship explanation

One member may select several gym days, favourite lessons and favourite drinks. These multi-value attributes are stored in separate tables so that each selection is represented by its own row. The foreign key in each related table connects the selection to its member record.

The foreign keys use `ON DELETE CASCADE`. When a member is deleted, the related preference records are deleted automatically. Unique constraints prevent the same member preference from being inserted more than once.

## Data integrity

- `member_id` is an auto-incrementing primary key in the `members` table.
- Required member fields are defined as `NOT NULL`.
- Age and weekly visit limits are checked by database constraints.
- Boolean fields store yes/no service indicators.
- `created_at` and `updated_at` record when the member record is created and modified.
- Foreign keys maintain referential integrity between parent and child records.

## Relationship summary

`members` has a one-to-many relationship with each of `member_days`, `member_favorite_lessons` and `member_favorite_drinks`.
