<?php

namespace pompom\craftmeditransfermailer;

use Craft;
use craft\base\Model;
use craft\base\Plugin;
use craft\events\RegisterComponentTypesEvent;
use craft\events\RegisterUrlRulesEvent;
use craft\services\Elements;
use craft\web\UrlManager;
use pompom\craftmeditransfermailer\models\Settings;
use pompom\craftmeditransfermailer\services;
use yii\base\Event;

/**
 * MediTransfer Mailer plugin
 *
 * @method static MediTransferMailer getInstance()
 * @method Settings getSettings()
 */
class MediTransferMailer extends Plugin
{
    public string $schemaVersion = '1.0.0';
    public bool $hasCpSettings = true;
    public bool $hasCpSection = true;

    public static function config(): array
    {
        return [
            'components' => [
                'postmark' => ['class' => services\PostmarkService::class],
                'campaigns' => ['class' => services\CampaignService::class],
                'templates' => ['class' => services\TemplateService::class],
                'tracking' => ['class' => services\TrackingService::class],
            ],
        ];
    }

    public function init(): void
    {
        parent::init();

        $this->attachEventHandlers();

        // Any code that creates an element query or loads Twig should be deferred until
        // after Craft is fully initialized, to avoid conflicts with other plugins/modules
        Craft::$app->onInit(function() {
            // Only create default templates if plugin is installed and tables exist
            if ($this->isInstalled && Craft::$app->getDb()->tableExists('{{%meditransfer_templates}}')) {
                $templateCount = \pompom\craftmeditransfermailer\records\EmailTemplateRecord::find()->count();
                if ($templateCount === 0) {
                    $this->templates->createDefaultTemplates();
                }
            }
        });
    }

    protected function createSettingsModel(): ?Model
    {
        return Craft::createObject(Settings::class);
    }

    protected function settingsHtml(): ?string
    {
        return Craft::$app->view->renderTemplate('_meditransfer-mailer/_settings.twig', [
            'plugin' => $this,
            'settings' => $this->getSettings(),
        ]);
    }

    public function getCpNavItem(): ?array
    {
        $item = parent::getCpNavItem();
        
        $item['subnav'] = [
            'campaigns' => ['label' => 'Kampagnen', 'url' => '_meditransfer-mailer/campaigns'],
            'templates' => ['label' => 'Vorlagen', 'url' => '_meditransfer-mailer/templates'],
            'analytics' => ['label' => 'Analysen', 'url' => '_meditransfer-mailer/analytics'],
            'settings' => ['label' => 'Einstellungen', 'url' => 'settings/plugins/_meditransfer-mailer'],
        ];
        
        return $item;
    }
    
    private function attachEventHandlers(): void
    {
        // Register CP routes
        Event::on(
            UrlManager::class,
            UrlManager::EVENT_REGISTER_CP_URL_RULES,
            function(RegisterUrlRulesEvent $event) {
                $event->rules = array_merge($event->rules, [
                    '_meditransfer-mailer/campaigns' => '_meditransfer-mailer/campaigns/index',
                    '_meditransfer-mailer/campaigns/new' => '_meditransfer-mailer/campaigns/edit',
                    '_meditransfer-mailer/campaigns/<campaignId:\d+>' => '_meditransfer-mailer/campaigns/edit',
                    '_meditransfer-mailer/campaigns/<campaignId:\d+>/recipients' => '_meditransfer-mailer/campaigns/recipients',
                    '_meditransfer-mailer/templates' => '_meditransfer-mailer/templates/index',
                    '_meditransfer-mailer/templates/new' => '_meditransfer-mailer/templates/edit',
                    '_meditransfer-mailer/templates/<templateId:\d+>' => '_meditransfer-mailer/templates/edit',
                    '_meditransfer-mailer/templates/<templateId:\d+>/preview' => '_meditransfer-mailer/templates/preview',
                    '_meditransfer-mailer/analytics' => '_meditransfer-mailer/analytics/index',
                    '_meditransfer-mailer/analytics/<campaignId:\d+>' => '_meditransfer-mailer/analytics/campaign',
                    '_meditransfer-mailer/analytics/<campaignId:\d+>/export' => '_meditransfer-mailer/analytics/export',
                ]);
            }
        );
        
        // Register site routes for webhooks
        Event::on(
            UrlManager::class,
            UrlManager::EVENT_REGISTER_SITE_URL_RULES,
            function(RegisterUrlRulesEvent $event) {
                $event->rules = array_merge($event->rules, [
                    '_meditransfer-mailer/webhooks/postmark' => '_meditransfer-mailer/webhooks/postmark',
                    '_meditransfer-mailer/unsubscribe' => '_meditransfer-mailer/webhooks/unsubscribe',
                ]);
            }
        );
    }
}
