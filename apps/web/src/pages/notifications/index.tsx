import { useState } from 'react';
import { FadeIn } from '@/components/motion/fade-in';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Bell, Mail, MessageSquare, Webhook, Plus, Trash2, Save } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

interface NotificationChannel {
  id: string;
  type: 'email' | 'slack' | 'discord' | 'webhook';
  name: string;
  enabled: boolean;
  config: {
    email?: string;
    webhookUrl?: string;
    channel?: string;
  };
}

const NotificationsPage = () => {
  const [channels, setChannels] = useState<NotificationChannel[]>([
    {
      id: '1',
      type: 'email',
      name: 'Primary Email',
      enabled: true,
      config: {
        email: 'user@example.com',
      },
    },
  ]);

  const [isAdding, setIsAdding] = useState(false);
  const [newChannelType, setNewChannelType] = useState<'email' | 'slack' | 'discord' | 'webhook'>(
    'email'
  );
  const [newChannelName, setNewChannelName] = useState('');
  const [newChannelConfig, setNewChannelConfig] = useState({
    email: '',
    webhookUrl: '',
    channel: '',
  });

  const getChannelIcon = (type: string) => {
    switch (type) {
      case 'email':
        return Mail;
      case 'slack':
      case 'discord':
        return MessageSquare;
      case 'webhook':
        return Webhook;
      default:
        return Bell;
    }
  };

  const getChannelLabel = (type: string) => {
    switch (type) {
      case 'email':
        return 'Email';
      case 'slack':
        return 'Slack';
      case 'discord':
        return 'Discord';
      case 'webhook':
        return 'Webhook';
      default:
        return 'Unknown';
    }
  };

  const handleAddChannel = () => {
    if (!newChannelName.trim()) return;

    const newChannel: NotificationChannel = {
      id: Date.now().toString(),
      type: newChannelType,
      name: newChannelName,
      enabled: true,
      config: newChannelConfig,
    };

    setChannels([...channels, newChannel]);
    setIsAdding(false);
    setNewChannelName('');
    setNewChannelConfig({ email: '', webhookUrl: '', channel: '' });
  };

  const handleDeleteChannel = (id: string) => {
    setChannels(channels.filter((ch) => ch.id !== id));
  };

  const handleToggleChannel = (id: string) => {
    setChannels(channels.map((ch) => (ch.id === id ? { ...ch, enabled: !ch.enabled } : ch)));
  };

  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto max-w-4xl space-y-8">
        <FadeIn>
          <div className="flex items-center gap-3">
            <Bell className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-4xl font-bold">Notification Channels</h1>
              <p className="text-muted-foreground mt-1">
                Configure how you receive notifications about webhook executions
              </p>
            </div>
          </div>
        </FadeIn>

        {/* Existing Channels */}
        <FadeIn delay={0.2}>
          <Card>
            <CardHeader>
              <CardTitle>Active Channels</CardTitle>
              <CardDescription>Manage your notification channels and preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {channels.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No notification channels configured</p>
                  <p className="text-sm mt-2">Add a channel to start receiving notifications</p>
                </div>
              ) : (
                channels.map((channel) => {
                  const Icon = getChannelIcon(channel.type);
                  return (
                    <Card key={channel.id} className="border">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-4 flex-1">
                            <div className="p-2 rounded-lg bg-primary/10">
                              <Icon className="h-5 w-5 text-primary" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-semibold">{channel.name}</h3>
                                <Badge variant="outline" className="text-xs">
                                  {getChannelLabel(channel.type)}
                                </Badge>
                                {channel.enabled ? (
                                  <Badge variant="default" className="text-xs bg-green-500">
                                    <CheckCircle2 className="h-3 w-3 mr-1" />
                                    Active
                                  </Badge>
                                ) : (
                                  <Badge variant="secondary" className="text-xs">
                                    <AlertCircle className="h-3 w-3 mr-1" />
                                    Inactive
                                  </Badge>
                                )}
                              </div>
                              <div className="text-sm text-muted-foreground mt-2">
                                {channel.type === 'email' && <p>{channel.config.email}</p>}
                                {channel.type === 'webhook' && (
                                  <p className="font-mono text-xs truncate">
                                    {channel.config.webhookUrl}
                                  </p>
                                )}
                                {(channel.type === 'slack' || channel.type === 'discord') && (
                                  <p className="font-mono text-xs truncate">
                                    {channel.config.webhookUrl || 'Not configured'}
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2">
                              <Label htmlFor={`toggle-${channel.id}`} className="text-xs">
                                {channel.enabled ? 'Enabled' : 'Disabled'}
                              </Label>
                              <Switch
                                id={`toggle-${channel.id}`}
                                checked={channel.enabled}
                                onCheckedChange={() => handleToggleChannel(channel.id)}
                              />
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteChannel(channel.id)}
                              className="text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </CardContent>
          </Card>
        </FadeIn>

        {/* Add New Channel */}
        <FadeIn delay={0.3}>
          <Card>
            <CardHeader>
              <CardTitle>Add Notification Channel</CardTitle>
              <CardDescription>
                Configure a new channel to receive webhook execution notifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!isAdding ? (
                <Button onClick={() => setIsAdding(true)} className="w-full" variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Channel
                </Button>
              ) : (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Channel Type</Label>
                    <Select
                      value={newChannelType}
                      onValueChange={(value: 'email' | 'slack' | 'discord' | 'webhook') =>
                        setNewChannelType(value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="email">
                          <div className="flex items-center gap-2">
                            <Mail className="h-4 w-4" />
                            Email
                          </div>
                        </SelectItem>
                        <SelectItem value="slack">
                          <div className="flex items-center gap-2">
                            <MessageSquare className="h-4 w-4" />
                            Slack
                          </div>
                        </SelectItem>
                        <SelectItem value="discord">
                          <div className="flex items-center gap-2">
                            <MessageSquare className="h-4 w-4" />
                            Discord
                          </div>
                        </SelectItem>
                        <SelectItem value="webhook">
                          <div className="flex items-center gap-2">
                            <Webhook className="h-4 w-4" />
                            Webhook
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Channel Name</Label>
                    <Input
                      placeholder="e.g., Team Notifications"
                      value={newChannelName}
                      onChange={(e) => setNewChannelName(e.target.value)}
                    />
                  </div>

                  {newChannelType === 'email' && (
                    <div className="space-y-2">
                      <Label>Email Address</Label>
                      <Input
                        type="email"
                        placeholder="notifications@example.com"
                        value={newChannelConfig.email}
                        onChange={(e) =>
                          setNewChannelConfig({ ...newChannelConfig, email: e.target.value })
                        }
                      />
                    </div>
                  )}

                  {(newChannelType === 'slack' ||
                    newChannelType === 'discord' ||
                    newChannelType === 'webhook') && (
                    <div className="space-y-2">
                      <Label>Webhook URL</Label>
                      <Input
                        type="url"
                        placeholder="https://hooks.slack.com/services/..."
                        value={newChannelConfig.webhookUrl}
                        onChange={(e) =>
                          setNewChannelConfig({ ...newChannelConfig, webhookUrl: e.target.value })
                        }
                      />
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Button onClick={handleAddChannel} className="flex-1">
                      <Save className="h-4 w-4 mr-2" />
                      Add Channel
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setIsAdding(false);
                        setNewChannelName('');
                        setNewChannelConfig({ email: '', webhookUrl: '', channel: '' });
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </div>
  );
};

export default NotificationsPage;
