import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from ..db.models import User, Payout, PayoutStatus, AuditLog, Pot
from ..utils.locks import user_lock

class PayoutService:
    def __init__(self, db: Session, house_rate: float = 0.03):
        self.db = db
        self.house_rate = house_rate

    @user_lock
    async def process_payout(self, user_id: int, amount: int, 
                           round_id: Optional[str] = None, 
                           reason: str = "win") -> Dict[str, Any]:
        """
        Process a payout transaction atomically.
        Uses database transaction and row locking to prevent double spending.
        """
        tx_ref = str(uuid.uuid4())
        
        try:
            # Start transaction
            user = self.db.execute(
                select(User).where(User.id == user_id).with_for_update()
            ).scalar_one()
            
            # Create payout record
            payout = Payout(
                tx_ref=tx_ref,
                user_id=user_id,
                amount=amount,
                round_id=round_id,
                status=PayoutStatus.PENDING.value
            )
            self.db.add(payout)
            
            # Update user balance
            old_balance = user.balance
            user.balance += amount
            new_balance = user.balance
            
            # Record house fee if applicable
            if reason == "win" and self.house_rate > 0:
                house_fee = int(amount * self.house_rate)
                self._add_to_pot(house_fee)
                net_amount = amount - house_fee
            else:
                net_amount = amount
            
            # Update payout status
            payout.status = PayoutStatus.DONE.value
            payout.completed_at = self.db.execute('SELECT NOW()').scalar()
            
            # Create audit log
            audit_log = AuditLog(
                actor_id='system',
                action=f'payout_{reason}',
                target=str(user_id),
                meta={
                    'tx_ref': tx_ref,
                    'amount': amount,
                    'net_amount': net_amount,
                    'round_id': round_id,
                    'old_balance': old_balance,
                    'new_balance': new_balance
                }
            )
            self.db.add(audit_log)
            
            self.db.commit()
            
            return {
                'success': True,
                'tx_ref': tx_ref,
                'amount': amount,
                'net_amount': net_amount,
                'new_balance': new_balance
            }
            
        except Exception as e:
            self.db.rollback()
            
            # Update payout record with error
            if 'payout' in locals():
                payout.status = PayoutStatus.FAILED.value
                payout.last_error = str(e)
                payout.attempts += 1
                self.db.commit()
            
            return {
                'success': False,
                'error': str(e),
                'tx_ref': tx_ref
            }

    def _add_to_pot(self, amount: int):
        """Add house fee to the pot."""
        pot = self.db.execute(select(Pot)).scalar()
        if not pot:
            pot = Pot(balance=0)
            self.db.add(pot)
        
        pot.balance += amount
        pot.updated_at = self.db.execute('SELECT NOW()').scalar()

    async def retry_failed_payouts(self, max_attempts: int = 3):
        """Retry failed payouts with exponential backoff."""
        failed_payouts = self.db.execute(
            select(Payout).where(
                Payout.status == PayoutStatus.FAILED.value,
                Payout.attempts < max_attempts
            )
        ).scalars().all()
        
        for payout in failed_payouts:
            result = await self.process_payout(
                payout.user_id, 
                payout.amount, 
                payout.round_id,
                "retry"
            )
            
            if not result['success']:
                payout.attempts += 1
                payout.last_error = result['error']
            else:
                payout.status = PayoutStatus.DONE.value
                payout.completed_at = self.db.execute('SELECT NOW()').scalar()
            
            self.db.commit()

    def get_payout_history(self, user_id: int, limit: int = 10):
        """Get payout history for a user."""
        return self.db.execute(
            select(Payout).where(
                Payout.user_id == user_id
            ).order_by(Payout.created_at.desc()).limit(limit)
        ).scalars().all()
