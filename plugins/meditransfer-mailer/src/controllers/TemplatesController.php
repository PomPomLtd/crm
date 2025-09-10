<?php

namespace pompom\craftmeditransfermailer\controllers;

use Craft;
use craft\web\Controller;
use pompom\craftmeditransfermailer\MediTransferMailer;
use pompom\craftmeditransfermailer\models\EmailTemplate;
use yii\web\Response;
use yii\web\NotFoundHttpException;

class TemplatesController extends Controller
{
    public function actionIndex(): Response
    {
        $plugin = MediTransferMailer::getInstance();
        $templates = $plugin->templates->getAllTemplates();
        
        return $this->renderTemplate('_meditransfer-mailer/templates/index', [
            'templates' => $templates,
        ]);
    }
    
    public function actionEdit(?int $templateId = null, ?EmailTemplate $template = null): Response
    {
        $plugin = MediTransferMailer::getInstance();
        $isNew = !$templateId;
        
        if (!$template) {
            if ($templateId) {
                $template = $plugin->templates->getTemplateById($templateId);
                if (!$template) {
                    throw new NotFoundHttpException('Vorlage nicht gefunden');
                }
            } else {
                $template = new EmailTemplate();
            }
        }
        
        return $this->renderTemplate('_meditransfer-mailer/templates/edit', [
            'template' => $template,
            'isNew' => $isNew,
        ]);
    }
    
    public function actionSave(): ?Response
    {
        $this->requirePostRequest();
        
        $plugin = MediTransferMailer::getInstance();
        $request = Craft::$app->getRequest();
        
        $templateId = $request->getBodyParam('templateId');
        
        if ($templateId) {
            $template = $plugin->templates->getTemplateById($templateId);
            if (!$template) {
                throw new NotFoundHttpException('Vorlage nicht gefunden');
            }
        } else {
            $template = new EmailTemplate();
        }
        
        // Populate template
        $template->name = $request->getBodyParam('name');
        $template->handle = $request->getBodyParam('handle');
        $template->subject = $request->getBodyParam('subject');
        $template->htmlContent = $request->getBodyParam('htmlContent');
        $template->textContent = $request->getBodyParam('textContent');
        $template->preheaderText = $request->getBodyParam('preheaderText');
        $template->isActive = (bool)$request->getBodyParam('isActive');
        
        // Parse custom variables
        $customVariables = $request->getBodyParam('customVariables');
        if ($customVariables) {
            $variables = [];
            foreach ($customVariables as $variable) {
                if (!empty($variable['name']) && !empty($variable['description'])) {
                    $variables[$variable['name']] = $variable['description'];
                }
            }
            $template->variables = $variables;
        }
        
        if (!$plugin->templates->saveTemplate($template)) {
            Craft::$app->getSession()->setError('Vorlage konnte nicht gespeichert werden');
            
            return $this->renderTemplate('_meditransfer-mailer/templates/edit', [
                'template' => $template,
                'isNew' => !$templateId,
            ]);
        }
        
        Craft::$app->getSession()->setNotice('Vorlage gespeichert');
        
        return $this->redirect('_meditransfer-mailer/templates/' . $template->id);
    }
    
    public function actionDelete(): Response
    {
        $this->requirePostRequest();
        $this->requireAcceptsJson();
        
        $templateId = Craft::$app->getRequest()->getRequiredBodyParam('templateId');
        $plugin = MediTransferMailer::getInstance();
        
        if (!$plugin->templates->deleteTemplate($templateId)) {
            return $this->asJson(['success' => false, 'message' => 'Vorlage konnte nicht gelöscht werden']);
        }
        
        return $this->asJson(['success' => true]);
    }
    
    public function actionPreview(int $templateId): Response
    {
        $plugin = MediTransferMailer::getInstance();
        $template = $plugin->templates->getTemplateById($templateId);
        
        if (!$template) {
            throw new NotFoundHttpException('Vorlage nicht gefunden');
        }
        
        // Sample data for preview
        $sampleData = [
            'recipientName' => 'Dr. Max Mustermann',
            'recipientEmail' => 'max.mustermann@example.com',
            'organizationName' => 'Musterklinik',
            'organizationType' => 'Krankenhaus',
            'currentDate' => date('d.m.Y'),
            'currentYear' => date('Y'),
            'unsubscribeUrl' => '#',
        ];
        
        $htmlContent = $template->parseContent($template->htmlContent, $sampleData);
        
        return $this->asRaw($htmlContent);
    }
}