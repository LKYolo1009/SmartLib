from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.borrowing_record import BorrowingRecord
from app.models.book_copy import BookCopy
from app.models.student import Student
from app.schemas.borrowing import BorrowCreate, BorrowUpdate
from .base import CRUDBase

class CRUDBorrowing(CRUDBase[BorrowingRecord, BorrowCreate, BorrowUpdate]):
    """借阅记录CRUD操作类"""

    def get(self, db: Session, borrow_id: int) -> Optional[BorrowingRecord]:
        """
        根据ID获取借阅记录
        :param db: 数据库会话
        :param borrow_id: 借阅ID
        :return: 借阅记录对象
        """
        return db.query(BorrowingRecord).filter(BorrowingRecord.borrow_id == borrow_id).first()
    
    def get_with_details(self, db: Session, borrow_id: int) -> Optional[BorrowingRecord]:
        """
        获取借阅记录及其关联的图书和学生信息
        :param db: 数据库会话
        :param borrow_id: 借阅ID
        :return: 借阅记录对象
        """
        return db.query(BorrowingRecord).options(
            joinedload(BorrowingRecord.copy).joinedload(BookCopy.book),
            joinedload(BorrowingRecord.student)
        ).filter(BorrowingRecord.borrow_id == borrow_id).first()
    
    def get_by_student(
        self, db: Session, *, student_id: int, skip: int = 0, limit: int = 100
    ) -> List[BorrowingRecord]:
        """
        获取学生的所有借阅记录
        :param db: 数据库会话
        :param student_id: 学生ID
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 借阅记录列表
        """
        return db.query(BorrowingRecord).filter(
            BorrowingRecord.student_id == student_id
        ).order_by(BorrowingRecord.borrow_date.desc()).offset(skip).limit(limit).all()
    
    def get_active_by_student(
        self, db: Session, *, student_id: int
    ) -> List[BorrowingRecord]:
        """
        获取学生的所有活跃借阅记录（未归还）
        :param db: 数据库会话
        :param student_id: 学生ID
        :return: 活跃借阅记录列表
        """
        return db.query(BorrowingRecord).filter(
            BorrowingRecord.student_id == student_id,
            BorrowingRecord.status == "borrowed"
        ).all()
    
    def get_by_copy(
        self, db: Session, *, copy_id: int, skip: int = 0, limit: int = 100
    ) -> List[BorrowingRecord]:
        """
        获取图书副本的所有借阅记录
        :param db: 数据库会话
        :param copy_id: 图书副本ID
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 借阅记录列表
        """
        return db.query(BorrowingRecord).filter(
            BorrowingRecord.copy_id == copy_id
        ).order_by(BorrowingRecord.borrow_date.desc()).offset(skip).limit(limit).all()
    
    def get_active_by_copy(
        self, db: Session, *, copy_id: int
    ) -> Optional[BorrowingRecord]:
        """
        获取图书副本的活跃借阅记录（未归还）
        :param db: 数据库会话
        :param copy_id: 图书副本ID
        :return: 活跃借阅记录
        """
        return db.query(BorrowingRecord).filter(
            BorrowingRecord.copy_id == copy_id,
            BorrowingRecord.status == "borrowed"
        ).first()
    
    def get_overdue(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[BorrowingRecord]:
        """
        获取所有逾期的借阅记录
        :param db: 数据库会话
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 逾期借阅记录列表
        """
        now = datetime.now()
        return db.query(BorrowingRecord).filter(
            BorrowingRecord.status == "borrowed",
            BorrowingRecord.due_date < now
        ).order_by(BorrowingRecord.due_date).offset(skip).limit(limit).all()
    
    def create_borrow(
        self, db: Session, *, obj_in: BorrowCreate
    ) -> BorrowingRecord:
        """
        创建新的借阅记录
        :param db: 数据库会话
        :param obj_in: 包含借阅数据的schema
        :return: 创建的借阅记录对象
        """
        # 检查图书副本是否存在
        copy = db.query(BookCopy).filter(BookCopy.copy_id == obj_in.copy_id).first()
        if not copy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="图书副本不存在"
            )
        
        # 检查图书是否可借
        if copy.status != "available":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="图书不可借阅"
            )
        
        # 检查学生是否存在
        student = db.query(Student).filter(Student.student_id == obj_in.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学生不存在"
            )
        
        # 检查学生状态
        if student.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学生状态不活跃"
            )
        
        # 检查学生借阅限制
        active_borrows = self.get_active_by_student(db, student_id=obj_in.student_id)
        if len(active_borrows) >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已达到最大借阅限制（3本）"
            )
        
        # 创建借阅记录
        db_obj = BorrowingRecord(
            copy_id=obj_in.copy_id,
            student_id=obj_in.student_id,
            due_date=obj_in.due_date,
            status="borrowed"
        )
        
        # 更新图书状态
        copy.status = "borrowed"
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def return_book(
        self, db: Session, *, borrow_id: int
    ) -> BorrowingRecord:
        """
        归还图书
        :param db: 数据库会话
        :param borrow_id: 借阅ID
        :return: 更新后的借阅记录对象
        """
        # 获取借阅记录
        borrow_record = self.get(db, borrow_id=borrow_id)
        if not borrow_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="借阅记录不存在"
            )
        
        if borrow_record.status == "returned":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="图书已归还"
            )
        
        # 获取图书副本
        copy = db.query(BookCopy).filter(BookCopy.copy_id == borrow_record.copy_id).first()
        
        # 更新借阅记录
        borrow_record.status = "returned"
        borrow_record.return_date = datetime.now()
        
        # 更新图书状态
        copy.status = "available"
        
        db.add(borrow_record)
        db.commit()
        db.refresh(borrow_record)
        return borrow_record
    
    def extend_due_date(
        self, db: Session, *, borrow_id: int, days: int = 14
    ) -> BorrowingRecord:
        """
        延长借阅期限
        :param db: 数据库会话
        :param borrow_id: 借阅ID
        :param days: 延长的天数
        :return: 更新后的借阅记录对象
        """
        borrow_record = self.get(db, borrow_id=borrow_id)
        if not borrow_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="借阅记录不存在"
            )
        
        if borrow_record.status != "borrowed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能延长活跃的借阅"
            )
        
        # 计算新的到期日期
        new_due_date = borrow_record.due_date + timedelta(days=days)
        
        # 更新记录
        borrow_record.extension_date = datetime.now()
        borrow_record.due_date = new_due_date
        
        db.add(borrow_record)
        db.commit()
        db.refresh(borrow_record)
        return borrow_record

# 创建借阅CRUD操作实例
borrowing_crud = CRUDBorrowing(BorrowingRecord)