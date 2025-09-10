<?php

namespace pompom\craftmeditransfermailer\controllers;

use Craft;
use craft\web\Controller;
use pompom\craftmeditransfermailer\MediTransferMailer;
use yii\web\Response;

class WebhooksController extends Controller
{
    protected array|bool|int $allowAnonymous = ['postmark'];
    public $enableCsrfValidation = false;
    
    public function actionPostmark(): Response
    {
        $request = Craft::$app->getRequest();
        
        if (!$request->getIsPost()) {
            return $this->asJson(['error' => 'Method not allowed'], 405);
        }
        
        $plugin = MediTransferMailer::getInstance();
        $postmarkService = $plugin->postmark;
        $trackingService = $plugin->tracking;
        
        // Get request data
        $rawBody = $request->getRawBody();
        $signature = $request->getHeaders()->get('X-Postmark-Signature');
        
        // Validate webhook signature if secret is configured
        if (!$postmarkService->validateWebhook($rawBody, $signature)) {
            Craft::warning('Invalid Postmark webhook signature', __METHOD__);
            return $this->asJson(['error' => 'Invalid signature'], 401);
        }
        
        // Parse JSON data
        try {
            $data = json_decode($rawBody, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                throw new \Exception('Invalid JSON: ' . json_last_error_msg());
            }
        } catch (\Exception $e) {
            Craft::error('Failed to parse Postmark webhook data: ' . $e->getMessage(), __METHOD__);
            return $this->asJson(['error' => 'Invalid JSON'], 400);
        }
        
        // Log the webhook for debugging
        Craft::info('Postmark webhook received: ' . $data['RecordType'] ?? 'Unknown event', __METHOD__);
        
        // Process the event
        try {
            $success = $trackingService->processWebhookEvent($data);
            
            if ($success) {
                return $this->asJson(['status' => 'ok']);
            } else {
                return $this->asJson(['error' => 'Failed to process event'], 500);
            }
            
        } catch (\Exception $e) {
            Craft::error('Failed to process Postmark webhook: ' . $e->getMessage(), __METHOD__);
            return $this->asJson(['error' => 'Processing failed'], 500);
        }
    }
    
    public function actionUnsubscribe(): Response
    {
        $request = Craft::$app->getRequest();
        $token = $request->getParam('token');
        
        if (!$token) {
            return $this->asErrorJson('Invalid token');
        }
        
        try {
            // Decode token
            $decoded = base64_decode($token);
            $parts = explode(':', $decoded, 2);
            
            if (count($parts) !== 2) {
                throw new \Exception('Invalid token format');
            }
            
            $recipientId = (int)$parts[0];
            $email = $parts[1];
            
            // Find recipient
            $recipientRecord = \pompom\craftmeditransfermailer\records\RecipientRecord::findOne($recipientId);
            
            if (!$recipientRecord || $recipientRecord->email !== $email) {
                throw new \Exception('Recipient not found');
            }
            
            // Mark as unsubscribed (you might want to create an unsubscribe table instead)
            $recipientRecord->status = 'unsubscribed';
            $recipientRecord->save();
            
            // Return simple HTML page
            return $this->asRaw('<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abgemeldet</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { color: #2c5aa0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Erfolgreich abgemeldet</h1>
        <p>Sie haben sich erfolgreich von unserem E-Mail-Verteiler abgemeldet.</p>
        <p>Ihre E-Mail-Adresse: <strong>' . htmlspecialchars($email) . '</strong></p>
        <p>Sie erhalten keine weiteren E-Mails von uns.</p>
    </div>
</body>
</html>');
            
        } catch (\Exception $e) {
            Craft::error('Failed to unsubscribe: ' . $e->getMessage(), __METHOD__);
            
            return $this->asRaw('<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fehler</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { color: #d32f2f; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Fehler</h1>
        <p>Es ist ein Fehler beim Abmelden aufgetreten.</p>
        <p>Bitte wenden Sie sich an unseren Support.</p>
    </div>
</body>
</html>');
        }
    }
}