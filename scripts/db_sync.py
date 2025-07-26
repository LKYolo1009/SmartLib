from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os
from pathlib import Path
import logging

# Add project root to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Now we can import from app
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_book_copy_status():
    """Sync book copy status with borrowing records to ensure data consistency"""
    try:
        # Create database engine
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # SQL script to sync book copy status with borrowing records
        sync_script = r"""
        -- Sync book copy status with borrowing records to ensure data consistency
        -- This query updates book_copies.status based on the latest borrowing record for each copy
        UPDATE book_copies 
        SET status = CASE 
            WHEN latest_borrow.return_date IS NULL AND latest_borrow.copy_id IS NOT NULL THEN 'borrowed'::book_status
            ELSE 'available'::book_status
        END
        FROM (
            SELECT DISTINCT ON (copy_id) 
                copy_id, 
                return_date,
                status
            FROM borrowing_records 
            ORDER BY copy_id, borrow_date DESC
        ) AS latest_borrow
        WHERE book_copies.copy_id = latest_borrow.copy_id;

        -- Update copies that have no borrowing records to 'available'
        UPDATE book_copies 
        SET status = 'available'::book_status
        WHERE copy_id NOT IN (
            SELECT DISTINCT copy_id FROM borrowing_records
        );
        """

        # Execute the sync script
        with SessionLocal() as db:
            logger.info("Starting book copy status synchronization...")
            db.execute(text(sync_script))
            db.commit()
            logger.info("Book copy status synchronization completed successfully!")
            
        return True
    except Exception as e:
        logger.error(f"Book copy status synchronization failed: {e}")
        return False

def verify_data_consistency():
    """Verify that book copy status is consistent with borrowing records"""
    try:
        # Create database engine
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # SQL script to check for inconsistencies
        verify_script = r"""
        -- Check for inconsistencies between book_copies and borrowing_records
        SELECT 
            bc.copy_id,
            bc.status as book_copy_status,
            br.return_date,
            CASE 
                WHEN br.return_date IS NULL AND br.copy_id IS NOT NULL THEN 'borrowed'::book_status
                ELSE 'available'::book_status
            END as expected_status,
            CASE 
                WHEN bc.status = CASE 
                    WHEN br.return_date IS NULL AND br.copy_id IS NOT NULL THEN 'borrowed'::book_status
                    ELSE 'available'::book_status
                END THEN 'Consistent'
                ELSE 'Inconsistent'
            END as consistency_status
        FROM book_copies bc
        LEFT JOIN (
            SELECT DISTINCT ON (copy_id) 
                copy_id, 
                return_date
            FROM borrowing_records 
            ORDER BY copy_id, borrow_date DESC
        ) br ON bc.copy_id = br.copy_id
        WHERE bc.status != CASE 
            WHEN br.return_date IS NULL AND br.copy_id IS NOT NULL THEN 'borrowed'::book_status
            ELSE 'available'::book_status
        END
        ORDER BY bc.copy_id;
        """

        # Execute the verification script
        with SessionLocal() as db:
            logger.info("Checking data consistency...")
            result = db.execute(text(verify_script))
            inconsistencies = result.fetchall()
            
            if inconsistencies:
                logger.warning(f"Found {len(inconsistencies)} inconsistencies:")
                for row in inconsistencies:
                    logger.warning(f"Copy ID {row[0]}: Book copy status='{row[1]}', Expected='{row[3]}'")
                return False
            else:
                logger.info("✓ All data is consistent!")
                return True
                
    except Exception as e:
        logger.error(f"Data consistency verification failed: {e}")
        return False

def debug_copy_status(copy_ids):
    """Debug specific copy IDs to understand their borrowing history"""
    try:
        # Create database engine
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # SQL script to debug copy status
        debug_script = r"""
        SELECT 
            bc.copy_id,
            bc.status as book_copy_status,
            br.borrow_id,
            br.matric_number,
            br.borrow_date,
            br.due_date,
            br.return_date,
            br.status as borrow_status
        FROM book_copies bc
        LEFT JOIN borrowing_records br ON bc.copy_id = br.copy_id
        WHERE bc.copy_id = ANY(:copy_ids)
        ORDER BY bc.copy_id, br.borrow_date DESC;
        """

        # Execute the debug script
        with SessionLocal() as db:
            logger.info(f"Debugging copy IDs: {copy_ids}")
            result = db.execute(text(debug_script), {"copy_ids": copy_ids})
            records = result.fetchall()
            
            for record in records:
                logger.info(f"Copy ID {record[0]}: Book status='{record[1]}', "
                          f"Borrow ID={record[2]}, Student={record[3]}, "
                          f"Borrow Date={record[4]}, Due Date={record[5]}, "
                          f"Return Date={record[6]}, Borrow Status={record[7]}")
                
    except Exception as e:
        logger.error(f"Debug failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "sync":
            sync_book_copy_status()
        elif command == "verify":
            verify_data_consistency()
        elif command == "fix":
            if sync_book_copy_status():
                verify_data_consistency()
        elif command == "debug":
            if len(sys.argv) > 2:
                copy_ids = [int(x) for x in sys.argv[2:]]
                debug_copy_status(copy_ids)
            else:
                print("Usage: python db_sync.py debug <copy_id1> <copy_id2> ...")
        else:
            print("Usage:")
            print("  python db_sync.py sync   - Sync book copy status")
            print("  python db_sync.py verify - Verify data consistency")
            print("  python db_sync.py fix    - Sync and verify (recommended)")
            print("  python db_sync.py debug <copy_ids> - Debug specific copy IDs")
    else:
        # Default: sync and verify
        if sync_book_copy_status():
            verify_data_consistency() 