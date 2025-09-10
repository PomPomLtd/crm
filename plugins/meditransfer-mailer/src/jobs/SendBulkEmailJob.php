<?php

namespace pompom\craftmeditransfermailer\jobs;

use Craft;
use craft\queue\BaseJob;
use craft\helpers\Db;
use craft\helpers\Json;
use pompom\craftmeditransfermailer\MediTransferMailer;
use pompom\craftmeditransfermailer\records\RecipientRecord;
use pompom\craftmeditransfermailer\records\CampaignRecord;
use pompom\craftmeditransfermailer\records\EmailTemplateRecord;

class SendBulkEmailJob extends BaseJob
{
    public int $campaignId;
    
    public function execute($queue): void
    {
        $plugin = MediTransferMailer::getInstance();
        $campaignService = $plugin->campaigns;
        $postmarkService = $plugin->postmark;
        
        $campaign = $campaignService->getCampaignById($this->campaignId);
        
        if (!$campaign) {
            throw new \Exception('Campaign not found');
        }
        
        // Get template
        $templateRecord = EmailTemplateRecord::findOne($campaign->templateId);
        if (!$templateRecord) {
            throw new \Exception('Email template not found');
        }
        
        // Get pending recipients
        $recipients = RecipientRecord::find()
            ->where(['campaignId' => $this->campaignId])
            ->andWhere(['status' => 'pending'])
            ->all();
        
        $totalRecipients = count($recipients);
        $settings = $plugin->getSettings();
        $batchSize = $settings->batchSize;
        
        // Process in batches
        $batches = array_chunk($recipients, $batchSize);
        $processedCount = 0;
        
        foreach ($batches as $batchIndex => $batch) {
            $this->setProgress($queue, $processedCount / $totalRecipients, 
                "Sende E-Mails... ({$processedCount}/{$totalRecipients})");
            
            $batchMessages = [];
            
            foreach ($batch as $recipient) {
                // Prepare variables for template
                $variables = [
                    'recipientName' => $recipient->name,
                    'recipientEmail' => $recipient->email,
                    'organizationName' => $recipient->organizationName,
                    'organizationType' => $recipient->organizationType,
                    'currentDate' => date('d.m.Y'),
                    'currentYear' => date('Y'),
                    'unsubscribeUrl' => $this->_getUnsubscribeUrl($recipient),
                ];
                
                // Add custom data variables
                if ($recipient->customData) {
                    $customData = Json::decode($recipient->customData);
                    $variables = array_merge($variables, $customData);
                }
                
                $batchMessages[] = [
                    'email' => $recipient->email,
                    'name' => $recipient->name,
                    'campaignId' => $this->campaignId,
                    'recipientId' => $recipient->id,
                    'variables' => $variables,
                ];
                
                // Mark as queued
                $recipient->status = 'queued';
                $recipient->save();
            }
            
            // Send batch via Postmark
            $result = $postmarkService->sendBatch(
                $batchMessages,
                $templateRecord->subject,
                $templateRecord->htmlContent,
                $templateRecord->textContent
            );
            
            if ($result['success']) {
                // Update recipient statuses
                foreach ($batch as $index => $recipient) {
                    $recipient->status = 'sent';
                    $recipient->sentDate = new \DateTime();
                    
                    if (isset($result['results'][$index])) {
                        $messageResult = $result['results'][$index];
                        if (isset($messageResult['MessageID'])) {
                            $recipient->postmarkMessageId = $messageResult['MessageID'];
                        }
                        if (isset($messageResult['ErrorCode']) && $messageResult['ErrorCode'] !== 0) {
                            $recipient->status = 'failed';
                            $recipient->errorMessage = $messageResult['Message'] ?? 'Unknown error';
                        }
                    }
                    
                    $recipient->save();
                }
                
                $processedCount += count($batch);
            } else {
                // Mark batch as failed
                foreach ($batch as $recipient) {
                    $recipient->status = 'failed';
                    $recipient->errorMessage = $result['error'] ?? 'Batch send failed';
                    $recipient->save();
                }
                
                Craft::error('Batch send failed: ' . ($result['error'] ?? 'Unknown error'), __METHOD__);
            }
            
            // Small delay between batches to respect rate limits
            if ($batchIndex < count($batches) - 1) {
                sleep(1);
            }
        }
        
        // Update campaign statistics
        $this->_updateCampaignStats($this->campaignId);
        
        // Mark campaign as completed
        Craft::$app->getDb()->createCommand()
            ->update(CampaignRecord::tableName(), [
                'status' => 'completed',
                'completedDate' => Db::prepareDateForDb(new \DateTime()),
            ], ['id' => $this->campaignId])
            ->execute();
    }
    
    protected function defaultDescription(): ?string
    {
        return 'Versende Kampagne #' . $this->campaignId;
    }
    
    private function _updateCampaignStats(int $campaignId): void
    {
        $sentCount = RecipientRecord::find()
            ->where(['campaignId' => $campaignId])
            ->andWhere(['status' => 'sent'])
            ->count();
        
        $failedCount = RecipientRecord::find()
            ->where(['campaignId' => $campaignId])
            ->andWhere(['status' => 'failed'])
            ->count();
        
        Craft::$app->getDb()->createCommand()
            ->update(CampaignRecord::tableName(), [
                'sentCount' => $sentCount,
            ], ['id' => $campaignId])
            ->execute();
    }
    
    private function _getUnsubscribeUrl($recipient): string
    {
        // Generate unique unsubscribe URL
        $token = base64_encode($recipient->id . ':' . $recipient->email);
        return Craft::$app->getSites()->getCurrentSite()->getBaseUrl() . 
               '_meditransfer-mailer/unsubscribe?token=' . $token;
    }
}