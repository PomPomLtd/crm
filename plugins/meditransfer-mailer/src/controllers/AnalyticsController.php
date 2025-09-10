<?php

namespace pompom\craftmeditransfermailer\controllers;

use Craft;
use craft\web\Controller;
use pompom\craftmeditransfermailer\MediTransferMailer;
use yii\web\Response;
use yii\web\NotFoundHttpException;

class AnalyticsController extends Controller
{
    public function actionIndex(): Response
    {
        $plugin = MediTransferMailer::getInstance();
        $campaigns = $plugin->campaigns->getAllCampaigns();
        
        // Calculate overall statistics
        $totalCampaigns = count($campaigns);
        $totalRecipients = 0;
        $totalSent = 0;
        $totalOpened = 0;
        $totalClicked = 0;
        
        foreach ($campaigns as $campaign) {
            $totalRecipients += $campaign->totalRecipients;
            $totalSent += $campaign->sentCount;
            $totalOpened += $campaign->openedCount;
            $totalClicked += $campaign->clickedCount;
        }
        
        $overallStats = [
            'totalCampaigns' => $totalCampaigns,
            'totalRecipients' => $totalRecipients,
            'totalSent' => $totalSent,
            'totalOpened' => $totalOpened,
            'totalClicked' => $totalClicked,
            'overallOpenRate' => $totalSent > 0 ? round(($totalOpened / $totalSent) * 100, 2) : 0,
            'overallClickRate' => $totalSent > 0 ? round(($totalClicked / $totalSent) * 100, 2) : 0,
        ];
        
        return $this->renderTemplate('_meditransfer-mailer/analytics/index', [
            'campaigns' => $campaigns,
            'overallStats' => $overallStats,
        ]);
    }
    
    public function actionCampaign(int $campaignId): Response
    {
        $plugin = MediTransferMailer::getInstance();
        $campaign = $plugin->campaigns->getCampaignById($campaignId);
        
        if (!$campaign) {
            throw new NotFoundHttpException('Kampagne nicht gefunden');
        }
        
        $trackingService = $plugin->tracking;
        
        // Get campaign statistics
        $stats = $trackingService->getCampaignStats($campaignId);
        
        // Get click data by URL
        $clicksByUrl = $trackingService->getClicksByUrl($campaignId);
        
        // Get event timeline
        $timeline = $trackingService->getEventTimeline($campaignId, 50);
        
        return $this->renderTemplate('_meditransfer-mailer/analytics/campaign', [
            'campaign' => $campaign,
            'stats' => $stats,
            'clicksByUrl' => $clicksByUrl,
            'timeline' => $timeline,
        ]);
    }
    
    public function actionExport(int $campaignId): Response
    {
        $plugin = MediTransferMailer::getInstance();
        $campaign = $plugin->campaigns->getCampaignById($campaignId);
        
        if (!$campaign) {
            throw new NotFoundHttpException('Kampagne nicht gefunden');
        }
        
        $recipients = $plugin->campaigns->getRecipients($campaignId);
        
        // Create CSV content
        $csv = "E-Mail,Name,Organisation,Typ,Status,Versendet,Geöffnet,Geklickt\n";
        
        foreach ($recipients as $recipient) {
            $csv .= sprintf(
                '"%s","%s","%s","%s","%s","%s","%s","%s"' . "\n",
                $recipient['email'],
                $recipient['name'] ?: '',
                $recipient['organizationName'] ?: '',
                $recipient['organizationType'] ?: '',
                $recipient['status'],
                $recipient['sentDate'] ? $recipient['sentDate']->format('d.m.Y H:i') : '',
                $recipient['openedDate'] ? $recipient['openedDate']->format('d.m.Y H:i') : '',
                $recipient['clickedDate'] ? $recipient['clickedDate']->format('d.m.Y H:i') : ''
            );
        }
        
        $filename = 'kampagne-' . $campaignId . '-' . date('Y-m-d') . '.csv';
        
        return Craft::$app->getResponse()->sendContentAsFile($csv, $filename, [
            'mimeType' => 'text/csv',
        ]);
    }
}