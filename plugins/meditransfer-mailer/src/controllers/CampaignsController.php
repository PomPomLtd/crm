<?php

namespace pompom\craftmeditransfermailer\controllers;

use Craft;
use craft\web\Controller;
use craft\helpers\Json;
use craft\elements\Entry;
use pompom\craftmeditransfermailer\MediTransferMailer;
use pompom\craftmeditransfermailer\models\Campaign;
use yii\web\Response;
use yii\web\NotFoundHttpException;

class CampaignsController extends Controller
{
    public function actionIndex(): Response
    {
        $plugin = MediTransferMailer::getInstance();
        $campaigns = $plugin->campaigns->getAllCampaigns();
        
        return $this->renderTemplate('_meditransfer-mailer/campaigns/index', [
            'campaigns' => $campaigns,
        ]);
    }
    
    public function actionEdit(?int $campaignId = null, ?Campaign $campaign = null): Response
    {
        $plugin = MediTransferMailer::getInstance();
        $isNew = !$campaignId;
        
        if (!$campaign) {
            if ($campaignId) {
                $campaign = $plugin->campaigns->getCampaignById($campaignId);
                if (!$campaign) {
                    throw new NotFoundHttpException('Kampagne nicht gefunden');
                }
            } else {
                $campaign = new Campaign();
            }
        }
        
        // Get available templates
        $templates = $plugin->templates->getAllTemplates();
        $templateOptions = ['' => 'Keine Vorlage'];
        foreach ($templates as $template) {
            if ($template->isActive) {
                $templateOptions[$template->id] = $template->name;
            }
        }
        
        // Get sections for recipient selection
        $entriesService = Craft::$app->getEntries();
        $sections = $entriesService->getAllSections();
        $sectionOptions = [];
        foreach ($sections as $section) {
            if ($section->type !== 'single') {
                $sectionOptions[] = [
                    'label' => $section->name,
                    'value' => $section->id,
                ];
            }
        }
        
        return $this->renderTemplate('_meditransfer-mailer/campaigns/edit', [
            'campaign' => $campaign,
            'isNew' => $isNew,
            'templateOptions' => $templateOptions,
            'sectionOptions' => $sectionOptions,
        ]);
    }
    
    public function actionSave(): ?Response
    {
        $this->requirePostRequest();
        
        $plugin = MediTransferMailer::getInstance();
        $request = Craft::$app->getRequest();
        
        $campaignId = $request->getBodyParam('campaignId');
        
        if ($campaignId) {
            $campaign = $plugin->campaigns->getCampaignById($campaignId);
            if (!$campaign) {
                throw new NotFoundHttpException('Kampagne nicht gefunden');
            }
        } else {
            $campaign = new Campaign();
        }
        
        // Populate campaign
        $campaign->name = $request->getBodyParam('name');
        $campaign->subject = $request->getBodyParam('subject');
        $campaign->templateId = $request->getBodyParam('templateId');
        $campaign->fromEmail = $request->getBodyParam('fromEmail');
        $campaign->fromName = $request->getBodyParam('fromName');
        $campaign->replyToEmail = $request->getBodyParam('replyToEmail');
        
        if (!$plugin->campaigns->saveCampaign($campaign)) {
            Craft::$app->getSession()->setError('Kampagne konnte nicht gespeichert werden');
            
            return $this->renderTemplate('_meditransfer-mailer/campaigns/edit', [
                'campaign' => $campaign,
                'isNew' => !$campaignId,
            ]);
        }
        
        Craft::$app->getSession()->setNotice('Kampagne gespeichert');
        
        return $this->redirect('_meditransfer-mailer/campaigns/' . $campaign->id);
    }
    
    public function actionDelete(): Response
    {
        $this->requirePostRequest();
        $this->requireAcceptsJson();
        
        $campaignId = Craft::$app->getRequest()->getRequiredBodyParam('campaignId');
        $plugin = MediTransferMailer::getInstance();
        
        if (!$plugin->campaigns->deleteCampaign($campaignId)) {
            return $this->asJson(['success' => false, 'message' => 'Kampagne konnte nicht gelöscht werden']);
        }
        
        return $this->asJson(['success' => true]);
    }
    
    public function actionRecipients(int $campaignId): Response
    {
        $plugin = MediTransferMailer::getInstance();
        $campaign = $plugin->campaigns->getCampaignById($campaignId);
        
        if (!$campaign) {
            throw new NotFoundHttpException('Kampagne nicht gefunden');
        }
        
        $recipients = $plugin->campaigns->getRecipients($campaignId);
        
        // Get sections for adding recipients
        $entriesService = Craft::$app->getEntries();
        $sections = $entriesService->getAllSections();
        $sectionOptions = [];
        foreach ($sections as $section) {
            if ($section->type !== 'single') {
                $sectionOptions[] = [
                    'label' => $section->name,
                    'value' => $section->id,
                ];
            }
        }
        
        return $this->renderTemplate('_meditransfer-mailer/campaigns/recipients', [
            'campaign' => $campaign,
            'recipients' => $recipients,
            'sectionOptions' => $sectionOptions,
        ]);
    }
    
    public function actionAddRecipients(): Response
    {
        $this->requirePostRequest();
        $this->requireAcceptsJson();
        
        $request = Craft::$app->getRequest();
        $campaignId = $request->getRequiredBodyParam('campaignId');
        $sectionId = $request->getBodyParam('sectionId');
        $entryIds = $request->getBodyParam('entryIds', []);
        
        $plugin = MediTransferMailer::getInstance();
        
        // If section is selected, get all entries from that section
        if ($sectionId && empty($entryIds)) {
            $entries = Entry::find()
                ->sectionId($sectionId)
                ->status('enabled')
                ->ids();
            $entryIds = $entries;
        }
        
        $count = $plugin->campaigns->addRecipientsFromEntries($campaignId, $entryIds);
        
        return $this->asJson([
            'success' => true,
            'message' => $count . ' Empfänger hinzugefügt',
            'count' => $count,
        ]);
    }
    
    public function actionSend(): Response
    {
        $this->requirePostRequest();
        $this->requireAcceptsJson();
        
        $campaignId = Craft::$app->getRequest()->getRequiredBodyParam('campaignId');
        $plugin = MediTransferMailer::getInstance();
        
        if (!$plugin->campaigns->sendCampaign($campaignId)) {
            return $this->asJson(['success' => false, 'message' => 'Kampagne konnte nicht gesendet werden']);
        }
        
        return $this->asJson(['success' => true, 'message' => 'Kampagne wird versendet']);
    }
    
    public function actionSchedule(): Response
    {
        $this->requirePostRequest();
        $this->requireAcceptsJson();
        
        $request = Craft::$app->getRequest();
        $campaignId = $request->getRequiredBodyParam('campaignId');
        $scheduledDate = $request->getRequiredBodyParam('scheduledDate');
        
        $plugin = MediTransferMailer::getInstance();
        $date = new \DateTime($scheduledDate);
        
        if (!$plugin->campaigns->scheduleCampaign($campaignId, $date)) {
            return $this->asJson(['success' => false, 'message' => 'Kampagne konnte nicht geplant werden']);
        }
        
        return $this->asJson(['success' => true, 'message' => 'Kampagne geplant']);
    }
    
    public function actionCancel(): Response
    {
        $this->requirePostRequest();
        $this->requireAcceptsJson();
        
        $campaignId = Craft::$app->getRequest()->getRequiredBodyParam('campaignId');
        $plugin = MediTransferMailer::getInstance();
        
        if (!$plugin->campaigns->cancelCampaign($campaignId)) {
            return $this->asJson(['success' => false, 'message' => 'Kampagne konnte nicht abgebrochen werden']);
        }
        
        return $this->asJson(['success' => true, 'message' => 'Kampagne abgebrochen']);
    }
}