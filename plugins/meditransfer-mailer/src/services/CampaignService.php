<?php

namespace pompom\craftmeditransfermailer\services;

use Craft;
use craft\base\Component;
use craft\db\Query;
use craft\elements\Entry;
use craft\helpers\Db;
use craft\helpers\Json;
use pompom\craftmeditransfermailer\MediTransferMailer;
use pompom\craftmeditransfermailer\models\Campaign;
use pompom\craftmeditransfermailer\records\CampaignRecord;
use pompom\craftmeditransfermailer\records\RecipientRecord;
use pompom\craftmeditransfermailer\jobs\SendBulkEmailJob;
use yii\base\Exception;

class CampaignService extends Component
{
    public function getAllCampaigns(): array
    {
        $records = CampaignRecord::find()
            ->orderBy(['dateCreated' => SORT_DESC])
            ->all();
        
        $campaigns = [];
        foreach ($records as $record) {
            $campaigns[] = $this->_createCampaignFromRecord($record);
        }
        
        return $campaigns;
    }
    
    public function getCampaignById(int $id): ?Campaign
    {
        $record = CampaignRecord::findOne($id);
        
        if (!$record) {
            return null;
        }
        
        return $this->_createCampaignFromRecord($record);
    }
    
    public function saveCampaign(Campaign $campaign): bool
    {
        $isNew = !$campaign->id;
        
        if (!$campaign->validate()) {
            return false;
        }
        
        $transaction = Craft::$app->getDb()->beginTransaction();
        
        try {
            if ($isNew) {
                $record = new CampaignRecord();
            } else {
                $record = CampaignRecord::findOne($campaign->id);
                if (!$record) {
                    throw new Exception('Campaign not found');
                }
            }
            
            $record->name = $campaign->name;
            $record->subject = $campaign->subject;
            $record->templateId = $campaign->templateId;
            $record->fromEmail = $campaign->fromEmail;
            $record->fromName = $campaign->fromName;
            $record->replyToEmail = $campaign->replyToEmail;
            $record->status = $campaign->status;
            $record->scheduledDate = Db::prepareDateForDb($campaign->scheduledDate);
            $record->settings = Json::encode($campaign->settings);
            
            if (!$record->save()) {
                throw new Exception('Could not save campaign record');
            }
            
            $campaign->id = $record->id;
            $campaign->uid = $record->uid;
            
            $transaction->commit();
            
            return true;
            
        } catch (\Exception $e) {
            $transaction->rollBack();
            Craft::error('Failed to save campaign: ' . $e->getMessage(), __METHOD__);
            return false;
        }
    }
    
    public function deleteCampaign(int $id): bool
    {
        $campaign = $this->getCampaignById($id);
        
        if (!$campaign || !$campaign->canDelete()) {
            return false;
        }
        
        $record = CampaignRecord::findOne($id);
        return $record && $record->delete();
    }
    
    public function addRecipientsFromEntries(int $campaignId, array $entryIds): int
    {
        $campaign = $this->getCampaignById($campaignId);
        
        if (!$campaign || !$campaign->canEdit()) {
            return 0;
        }
        
        $entries = Entry::find()
            ->id($entryIds)
            ->status('enabled')
            ->all();
        
        $count = 0;
        $existingEmails = $this->_getExistingRecipientEmails($campaignId);
        
        foreach ($entries as $entry) {
            // Extract email from entry fields - adjust based on your field structure
            $email = $entry->getFieldValue('email') ?? $entry->getFieldValue('emailAddress') ?? null;
            
            if (!$email || in_array($email, $existingEmails)) {
                continue;
            }
            
            $record = new RecipientRecord();
            $record->campaignId = $campaignId;
            $record->elementId = $entry->id;
            $record->email = $email;
            $record->name = $entry->title ?? $entry->getFieldValue('name') ?? '';
            $record->organizationName = $entry->getFieldValue('organizationName') ?? $entry->getFieldValue('companyName') ?? '';
            $record->organizationType = $entry->getFieldValue('organizationType') ?? $entry->getFieldValue('type') ?? '';
            
            // Store additional custom data
            $customData = [
                'entryId' => $entry->id,
                'sectionHandle' => $entry->section->handle,
                'typeHandle' => $entry->type->handle,
            ];
            $record->customData = Json::encode($customData);
            
            if ($record->save()) {
                $count++;
                $existingEmails[] = $email;
            }
        }
        
        // Update campaign recipient count
        $this->updateRecipientCount($campaignId);
        
        return $count;
    }
    
    public function updateRecipientCount(int $campaignId): void
    {
        $count = RecipientRecord::find()
            ->where(['campaignId' => $campaignId])
            ->count();
        
        Craft::$app->getDb()->createCommand()
            ->update(CampaignRecord::tableName(), 
                ['totalRecipients' => $count],
                ['id' => $campaignId]
            )
            ->execute();
    }
    
    public function sendCampaign(int $campaignId, bool $immediate = false): bool
    {
        $campaign = $this->getCampaignById($campaignId);
        
        if (!$campaign || !$campaign->canSend()) {
            return false;
        }
        
        // Update campaign status
        $campaign->status = 'sending';
        $this->saveCampaign($campaign);
        
        // Create queue job for sending
        $job = new SendBulkEmailJob([
            'campaignId' => $campaignId,
        ]);
        
        if ($immediate) {
            // Execute immediately (for testing)
            $job->execute(Craft::$app->getQueue());
        } else {
            // Add to queue
            Craft::$app->getQueue()->push($job);
        }
        
        return true;
    }
    
    public function scheduleCampaign(int $campaignId, \DateTime $scheduleDate): bool
    {
        $campaign = $this->getCampaignById($campaignId);
        
        if (!$campaign || !$campaign->canEdit()) {
            return false;
        }
        
        $campaign->status = 'scheduled';
        $campaign->scheduledDate = $scheduleDate;
        
        if ($this->saveCampaign($campaign)) {
            // Create delayed queue job
            $delay = $scheduleDate->getTimestamp() - time();
            
            if ($delay > 0) {
                $job = new SendBulkEmailJob([
                    'campaignId' => $campaignId,
                ]);
                
                Craft::$app->getQueue()->delay($delay)->push($job);
            }
            
            return true;
        }
        
        return false;
    }
    
    public function cancelCampaign(int $campaignId): bool
    {
        $campaign = $this->getCampaignById($campaignId);
        
        if (!$campaign || !$campaign->canCancel()) {
            return false;
        }
        
        $campaign->status = 'draft';
        $campaign->scheduledDate = null;
        
        return $this->saveCampaign($campaign);
    }
    
    public function getRecipients(int $campaignId): array
    {
        $records = RecipientRecord::find()
            ->where(['campaignId' => $campaignId])
            ->orderBy(['dateCreated' => SORT_ASC])
            ->all();
        
        $recipients = [];
        foreach ($records as $record) {
            $recipient = [
                'id' => $record->id,
                'email' => $record->email,
                'name' => $record->name,
                'organizationName' => $record->organizationName,
                'organizationType' => $record->organizationType,
                'status' => $record->status,
                'sentDate' => $record->sentDate,
                'openedDate' => $record->openedDate,
                'clickedDate' => $record->clickedDate,
            ];
            
            if ($record->customData) {
                $recipient['customData'] = Json::decode($record->customData);
            }
            
            $recipients[] = $recipient;
        }
        
        return $recipients;
    }
    
    private function _createCampaignFromRecord(CampaignRecord $record): Campaign
    {
        $campaign = new Campaign();
        $campaign->id = $record->id;
        $campaign->uid = $record->uid;
        $campaign->name = $record->name;
        $campaign->subject = $record->subject;
        $campaign->templateId = $record->templateId;
        $campaign->fromEmail = $record->fromEmail;
        $campaign->fromName = $record->fromName;
        $campaign->replyToEmail = $record->replyToEmail;
        $campaign->status = $record->status;
        $campaign->scheduledDate = $record->scheduledDate ? new \DateTime($record->scheduledDate) : null;
        $campaign->completedDate = $record->completedDate ? new \DateTime($record->completedDate) : null;
        $campaign->sentCount = $record->sentCount;
        $campaign->totalRecipients = $record->totalRecipients;
        $campaign->openedCount = $record->openedCount;
        $campaign->clickedCount = $record->clickedCount;
        $campaign->bouncedCount = $record->bouncedCount;
        $campaign->settings = $record->settings ? Json::decode($record->settings) : [];
        $campaign->dateCreated = new \DateTime($record->dateCreated);
        $campaign->dateUpdated = new \DateTime($record->dateUpdated);
        
        return $campaign;
    }
    
    private function _getExistingRecipientEmails(int $campaignId): array
    {
        return RecipientRecord::find()
            ->select(['email'])
            ->where(['campaignId' => $campaignId])
            ->column();
    }
}