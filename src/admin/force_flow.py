import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from ..db.models import ForcedAction, ForcedActionStatus, AuditLog
from ..services.rng_service import RNGService

class ForceFlowService:
    def __init__(self, db: Session, rng_service: RNGService, admin_ids: List[int], confirm_threshold: int = 2):
        self.db = db
        self.rng_service = rng_service
        self.admin_ids = admin_ids
        self.confirm_threshold = confirm_threshold

    def request_force(self, chat_id: int, requested_by: int, forced_value: str) -> Dict:
        """Request a forced outcome for a chat."""
        if requested_by not in self.admin_ids:
            raise ValueError("Only admins can request forced outcomes")
            
        if forced_value not in ['small', 'big', 'even', 'odd']:
            raise ValueError("Invalid forced value")
        
        # Create forced action request
        forced_action = ForcedAction(
            chat_id=chat_id,
            requested_by=requested_by,
            forced_value=forced_value,
            confirmations=json.dumps([]),
            required_confirmations=self.confirm_threshold,
            status=ForcedActionStatus.PENDING.value,
            audit_ref=f"force_{chat_id}_{datetime.utcnow().timestamp()}"
        )
        
        self.db.add(forced_action)
        
        # Create audit log
        audit_log = AuditLog(
            actor_id=requested_by,
            action='force_requested',
            target=str(chat_id),
            meta={
                'forced_value': forced_value,
                'forced_action_id': forced_action.id
            }
        )
        self.db.add(audit_log)
        
        self.db.commit()
        
        return {
            'success': True,
            'forced_action_id': forced_action.id,
            'required_confirmations': self.confirm_threshold
        }

    def confirm_force(self, forced_action_id: int, confirmed_by: int) -> Dict:
        """Confirm a forced action request."""
        if confirmed_by not in self.admin_ids:
            raise ValueError("Only admins can confirm forced outcomes")
        
        forced_action = self.db.execute(
            f"SELECT * FROM forced_actions WHERE id = {forced_action_id} FOR UPDATE"
        ).first()
        
        if not forced_action:
            raise ValueError("Forced action not found")
        
        if forced_action.status != ForcedActionStatus.PENDING.value:
            raise ValueError("Forced action is no longer pending")
        
        # Parse existing confirmations
        confirmations = json.loads(forced_action.confirmations)
        
        # Check if already confirmed by this admin
        if any(conf['admin_id'] == confirmed_by for conf in confirmations):
            raise ValueError("Already confirmed by this admin")
        
        # Add confirmation
        confirmations.append({
            'admin_id': confirmed_by,
            'confirmed_at': datetime.utcnow().isoformat()
        })
        
        forced_action.confirmations = json.dumps(confirmations)
        
        # Check if threshold reached
        if len(confirmations) >= forced_action.required_confirmations:
            forced_action.status = ForcedActionStatus.APPROVED.value
            
            # Generate forced seed for next round
            round_id = f"{forced_action.chat_id}_forced_{forced_action.id}"
            forced_seed_result = self.rng_service.generate_forced_seed(
                round_id, forced_action.forced_value
            )
            
            if forced_seed_result:
                server_seed, commitment = forced_seed_result
                
                # Store the forced seed (in real implementation, you'd need to
                # ensure this seed is used for the next round in that chat)
                self.rng_service.encrypt_and_store_seed(
                    self.db, round_id, server_seed, commitment
                )
                
                forced_action.applied_round = round_id
                forced_action.status = ForcedActionStatus.APPLIED.value
                
                # Create audit log for application
                audit_log = AuditLog(
                    actor_id='system',
                    action='force_applied',
                    target=str(forced_action.chat_id),
                    meta={
                        'forced_action_id': forced_action.id,
                        'forced_value': forced_action.forced_value,
                        'applied_round': round_id
                    }
                )
                self.db.add(audit_log)
        
        self.db.commit()
        
        return {
            'success': True,
            'forced_action_id': forced_action.id,
            'confirmations_count': len(confirmations),
            'required_confirmations': forced_action.required_confirmations,
            'status': forced_action.status
        }

    def get_pending_actions(self, chat_id: Optional[int] = None) -> List[ForcedAction]:
        """Get pending forced actions."""
        query = f"SELECT * FROM forced_actions WHERE status = '{ForcedActionStatus.PENDING.value}'"
        if chat_id:
            query += f" AND chat_id = {chat_id}"
        
        return self.db.execute(query).fetchall()

    def get_force_history(self, chat_id: Optional[int] = None, limit: int = 10) -> List[ForcedAction]:
        """Get force action history."""
        query = "SELECT * FROM forced_actions WHERE 1=1"
        if chat_id:
            query += f" AND chat_id = {chat_id}"
        query += f" ORDER BY requested_at DESC LIMIT {limit}"
        
        return self.db.execute(query).fetchall()
