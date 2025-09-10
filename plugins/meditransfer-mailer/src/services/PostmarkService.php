<?php

namespace pompom\craftmeditransfermailer\services;

use Craft;
use craft\base\Component;
use pompom\craftmeditransfermailer\MediTransferMailer;
use Postmark\PostmarkClient;
use Postmark\Models\PostmarkMessage;
use Postmark\Models\PostmarkAttachment;

class PostmarkService extends Component
{
    private ?PostmarkClient $client = null;
    
    public function getClient(): PostmarkClient
    {
        if ($this->client === null) {
            $settings = MediTransferMailer::getInstance()->getSettings();
            $this->client = new PostmarkClient($settings->postmarkServerToken);
        }
        
        return $this->client;
    }
    
    public function sendEmail(array $recipient, string $subject, string $htmlBody, string $textBody = '', array $variables = []): array
    {
        $settings = MediTransferMailer::getInstance()->getSettings();
        
        try {
            $message = new PostmarkMessage();
            $message->setFrom($settings->fromEmail, $settings->fromName);
            $message->setTo($recipient['email'], $recipient['name'] ?? '');
            $message->setSubject($this->parseVariables($subject, $variables));
            $message->setHtmlBody($this->parseVariables($htmlBody, $variables));
            
            if (!empty($textBody)) {
                $message->setTextBody($this->parseVariables($textBody, $variables));
            }
            
            if (!empty($settings->replyToEmail)) {
                $message->setReplyTo($settings->replyToEmail);
            }
            
            // Add tracking pixel if enabled
            if ($settings->enableTracking) {
                $message->setTrackOpens(true);
                $message->setTrackLinks('HtmlAndText');
            }
            
            // Add custom headers for campaign tracking
            if (isset($recipient['campaignId']) && isset($recipient['recipientId'])) {
                $message->addHeader('X-Campaign-ID', (string)$recipient['campaignId']);
                $message->addHeader('X-Recipient-ID', (string)$recipient['recipientId']);
            }
            
            // Send via Postmark
            if ($settings->testMode) {
                // In test mode, don't actually send
                Craft::info('Test mode: Would send email to ' . $recipient['email'], __METHOD__);
                return [
                    'success' => true,
                    'messageId' => 'test-' . uniqid(),
                    'testMode' => true,
                ];
            }
            
            $result = $this->getClient()->sendEmailWithTemplate($message);
            
            return [
                'success' => true,
                'messageId' => $result->getMessageId(),
                'submittedAt' => $result->getSubmittedAt(),
            ];
            
        } catch (\Exception $e) {
            Craft::error('Failed to send email: ' . $e->getMessage(), __METHOD__);
            return [
                'success' => false,
                'error' => $e->getMessage(),
            ];
        }
    }
    
    public function sendBatch(array $recipients, string $subject, string $htmlBody, string $textBody = ''): array
    {
        $settings = MediTransferMailer::getInstance()->getSettings();
        $messages = [];
        
        foreach ($recipients as $recipient) {
            $message = [
                'From' => $settings->fromEmail,
                'To' => $recipient['email'],
                'Subject' => $this->parseVariables($subject, $recipient['variables'] ?? []),
                'HtmlBody' => $this->parseVariables($htmlBody, $recipient['variables'] ?? []),
                'TextBody' => $this->parseVariables($textBody, $recipient['variables'] ?? []),
                'TrackOpens' => $settings->enableTracking,
                'TrackLinks' => $settings->enableTracking ? 'HtmlAndText' : 'None',
                'Metadata' => [
                    'campaign_id' => (string)($recipient['campaignId'] ?? ''),
                    'recipient_id' => (string)($recipient['recipientId'] ?? ''),
                ],
            ];
            
            if (!empty($settings->replyToEmail)) {
                $message['ReplyTo'] = $settings->replyToEmail;
            }
            
            $messages[] = $message;
        }
        
        try {
            if ($settings->testMode) {
                Craft::info('Test mode: Would send batch of ' . count($messages) . ' emails', __METHOD__);
                return [
                    'success' => true,
                    'sent' => count($messages),
                    'testMode' => true,
                ];
            }
            
            // Send in batches (Postmark allows max 500 per batch)
            $results = [];
            $chunks = array_chunk($messages, min($settings->batchSize, 500));
            
            foreach ($chunks as $chunk) {
                $response = $this->getClient()->sendEmailBatch($chunk);
                $results = array_merge($results, $response);
            }
            
            return [
                'success' => true,
                'results' => $results,
                'sent' => count($results),
            ];
            
        } catch (\Exception $e) {
            Craft::error('Failed to send batch emails: ' . $e->getMessage(), __METHOD__);
            return [
                'success' => false,
                'error' => $e->getMessage(),
            ];
        }
    }
    
    public function getMessageDetails(string $messageId): ?array
    {
        try {
            $details = $this->getClient()->getOutboundMessageDetails($messageId);
            return [
                'messageId' => $details->MessageID,
                'status' => $details->Status,
                'to' => $details->To,
                'subject' => $details->Subject,
                'submittedAt' => $details->SubmittedAt,
                'events' => $details->MessageEvents ?? [],
            ];
        } catch (\Exception $e) {
            Craft::error('Failed to get message details: ' . $e->getMessage(), __METHOD__);
            return null;
        }
    }
    
    public function validateWebhook(string $payload, string $signature): bool
    {
        $settings = MediTransferMailer::getInstance()->getSettings();
        
        if (empty($settings->webhookSecret)) {
            return true; // No secret configured, skip validation
        }
        
        $expectedSignature = base64_encode(hash_hmac('sha256', $payload, $settings->webhookSecret, true));
        return hash_equals($expectedSignature, $signature);
    }
    
    public function processWebhookEvent(array $data): bool
    {
        $event = $data['RecordType'] ?? '';
        $messageId = $data['MessageID'] ?? '';
        
        switch ($event) {
            case 'Delivery':
                return $this->handleDeliveryEvent($data);
            case 'Open':
                return $this->handleOpenEvent($data);
            case 'Click':
                return $this->handleClickEvent($data);
            case 'Bounce':
                return $this->handleBounceEvent($data);
            case 'SpamComplaint':
                return $this->handleSpamComplaintEvent($data);
            default:
                Craft::warning('Unknown webhook event type: ' . $event, __METHOD__);
                return false;
        }
    }
    
    protected function handleDeliveryEvent(array $data): bool
    {
        // Implementation will be added with tracking service
        return true;
    }
    
    protected function handleOpenEvent(array $data): bool
    {
        // Implementation will be added with tracking service
        return true;
    }
    
    protected function handleClickEvent(array $data): bool
    {
        // Implementation will be added with tracking service
        return true;
    }
    
    protected function handleBounceEvent(array $data): bool
    {
        // Implementation will be added with tracking service
        return true;
    }
    
    protected function handleSpamComplaintEvent(array $data): bool
    {
        // Implementation will be added with tracking service
        return true;
    }
    
    protected function parseVariables(string $content, array $variables): string
    {
        foreach ($variables as $key => $value) {
            $content = str_replace('{{' . $key . '}}', $value, $content);
        }
        return $content;
    }
}