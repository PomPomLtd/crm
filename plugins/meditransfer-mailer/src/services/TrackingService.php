<?php

namespace pompom\craftmeditransfermailer\services;

use Craft;
use craft\base\Component;
use craft\helpers\Json;
use pompom\craftmeditransfermailer\records\EmailTrackingRecord;
use pompom\craftmeditransfermailer\records\RecipientRecord;
use pompom\craftmeditransfermailer\records\CampaignRecord;

class TrackingService extends Component
{
    public function recordEvent(string $event, int $campaignId, int $recipientId, array $eventData = []): bool
    {
        try {
            $record = new EmailTrackingRecord();
            $record->campaignId = $campaignId;
            $record->recipientId = $recipientId;
            $record->messageId = $eventData['MessageID'] ?? null;
            $record->event = $event;
            $record->eventData = Json::encode($eventData);
            $record->ipAddress = $eventData['IP'] ?? null;
            $record->userAgent = $eventData['UserAgent'] ?? null;
            $record->clickedUrl = $eventData['OriginalLink'] ?? null;
            $record->timestamp = new \DateTime($eventData['ReceivedAt'] ?? 'now');
            
            if ($record->save()) {
                // Update recipient status based on event
                $this->_updateRecipientStatus($recipientId, $event, $eventData);
                return true;
            }
            
            return false;
            
        } catch (\Exception $e) {
            Craft::error('Failed to record tracking event: ' . $e->getMessage(), __METHOD__);
            return false;
        }
    }
    
    public function processWebhookEvent(array $data): bool
    {
        $event = $data['RecordType'] ?? '';
        $messageId = $data['MessageID'] ?? '';
        
        // Find recipient by message ID
        $recipient = RecipientRecord::find()
            ->where(['postmarkMessageId' => $messageId])
            ->one();
        
        if (!$recipient) {
            Craft::warning('Recipient not found for message ID: ' . $messageId, __METHOD__);
            return false;
        }
        
        // Record the event
        $success = $this->recordEvent($event, $recipient->campaignId, $recipient->id, $data);
        
        if ($success) {
            // Update campaign statistics
            $this->_updateCampaignStats($recipient->campaignId);
        }
        
        return $success;
    }
    
    public function getCampaignEvents(int $campaignId, ?string $event = null): array
    {
        $query = EmailTrackingRecord::find()
            ->where(['campaignId' => $campaignId])
            ->orderBy(['timestamp' => SORT_DESC]);
        
        if ($event) {
            $query->andWhere(['event' => $event]);
        }
        
        $records = $query->all();
        
        $events = [];
        foreach ($records as $record) {
            $events[] = [
                'id' => $record->id,
                'recipientId' => $record->recipientId,
                'messageId' => $record->messageId,
                'event' => $record->event,
                'eventData' => $record->eventData ? Json::decode($record->eventData) : [],
                'ipAddress' => $record->ipAddress,
                'userAgent' => $record->userAgent,
                'clickedUrl' => $record->clickedUrl,
                'timestamp' => new \DateTime($record->timestamp),
            ];
        }
        
        return $events;
    }
    
    public function getCampaignStats(int $campaignId): array
    {
        $campaign = CampaignRecord::findOne($campaignId);
        if (!$campaign) {
            return [];
        }
        
        // Get event counts
        $eventCounts = EmailTrackingRecord::find()
            ->select(['event', 'COUNT(*) as count'])
            ->where(['campaignId' => $campaignId])
            ->groupBy(['event'])
            ->asArray()
            ->all();
        
        $stats = [
            'totalRecipients' => $campaign->totalRecipients,
            'sentCount' => $campaign->sentCount,
            'openedCount' => $campaign->openedCount,
            'clickedCount' => $campaign->clickedCount,
            'bouncedCount' => $campaign->bouncedCount,
            'events' => [],
        ];
        
        foreach ($eventCounts as $eventCount) {
            $stats['events'][$eventCount['event']] = (int)$eventCount['count'];
        }
        
        // Calculate rates
        if ($campaign->sentCount > 0) {
            $stats['openRate'] = round(($campaign->openedCount / $campaign->sentCount) * 100, 2);
            $stats['clickRate'] = round(($campaign->clickedCount / $campaign->sentCount) * 100, 2);
            $stats['bounceRate'] = round(($campaign->bouncedCount / $campaign->sentCount) * 100, 2);
        } else {
            $stats['openRate'] = 0;
            $stats['clickRate'] = 0;
            $stats['bounceRate'] = 0;
        }
        
        return $stats;
    }
    
    public function getClicksByUrl(int $campaignId): array
    {
        $records = EmailTrackingRecord::find()
            ->select(['clickedUrl', 'COUNT(*) as count'])
            ->where(['campaignId' => $campaignId])
            ->andWhere(['event' => 'Click'])
            ->andWhere(['not', ['clickedUrl' => null]])
            ->groupBy(['clickedUrl'])
            ->orderBy(['count' => SORT_DESC])
            ->asArray()
            ->all();
        
        $clicks = [];
        foreach ($records as $record) {
            $clicks[] = [
                'url' => $record['clickedUrl'],
                'clicks' => (int)$record['count'],
            ];
        }
        
        return $clicks;
    }
    
    public function getEventTimeline(int $campaignId, int $limit = 100): array
    {
        $records = EmailTrackingRecord::find()
            ->where(['campaignId' => $campaignId])
            ->orderBy(['timestamp' => SORT_DESC])
            ->limit($limit)
            ->all();
        
        $timeline = [];
        foreach ($records as $record) {
            $recipient = RecipientRecord::findOne($record->recipientId);
            
            $timeline[] = [
                'event' => $record->event,
                'timestamp' => new \DateTime($record->timestamp),
                'recipientEmail' => $recipient ? $recipient->email : 'Unknown',
                'recipientName' => $recipient ? $recipient->name : null,
                'eventData' => $record->eventData ? Json::decode($record->eventData) : [],
                'clickedUrl' => $record->clickedUrl,
            ];
        }
        
        return $timeline;
    }
    
    private function _updateRecipientStatus(int $recipientId, string $event, array $eventData): void
    {
        $recipient = RecipientRecord::findOne($recipientId);
        if (!$recipient) {
            return;
        }
        
        $updateFields = [];
        
        switch ($event) {
            case 'Delivery':
                $updateFields['status'] = 'delivered';
                break;
                
            case 'Open':
                if (!$recipient->openedDate) {
                    $updateFields['status'] = 'opened';
                    $updateFields['openedDate'] = new \DateTime($eventData['ReceivedAt'] ?? 'now');
                }
                break;
                
            case 'Click':
                if (!$recipient->clickedDate) {
                    $updateFields['status'] = 'clicked';
                    $updateFields['clickedDate'] = new \DateTime($eventData['ReceivedAt'] ?? 'now');
                }
                break;
                
            case 'Bounce':
                $updateFields['status'] = 'bounced';
                $updateFields['bouncedDate'] = new \DateTime($eventData['ReceivedAt'] ?? 'now');
                $updateFields['errorMessage'] = $eventData['Description'] ?? 'Email bounced';
                break;
                
            case 'SpamComplaint':
                $updateFields['status'] = 'bounced';
                $updateFields['errorMessage'] = 'Spam complaint';
                break;
        }
        
        if (!empty($updateFields)) {
            Craft::$app->getDb()->createCommand()
                ->update(RecipientRecord::tableName(), $updateFields, ['id' => $recipientId])
                ->execute();
        }
    }
    
    private function _updateCampaignStats(int $campaignId): void
    {
        // Count different recipient statuses
        $openedCount = RecipientRecord::find()
            ->where(['campaignId' => $campaignId])
            ->andWhere(['in', 'status', ['opened', 'clicked']])
            ->count();
        
        $clickedCount = RecipientRecord::find()
            ->where(['campaignId' => $campaignId])
            ->andWhere(['status' => 'clicked'])
            ->count();
        
        $bouncedCount = RecipientRecord::find()
            ->where(['campaignId' => $campaignId])
            ->andWhere(['status' => 'bounced'])
            ->count();
        
        // Update campaign record
        Craft::$app->getDb()->createCommand()
            ->update(CampaignRecord::tableName(), [
                'openedCount' => $openedCount,
                'clickedCount' => $clickedCount,
                'bouncedCount' => $bouncedCount,
            ], ['id' => $campaignId])
            ->execute();
    }
}