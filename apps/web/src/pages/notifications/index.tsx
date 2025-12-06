import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { FadeIn } from '@/components/motion/fade-in';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Bell,
  Mail,
  MessageSquare,
  Webhook,
  Plus,
  Trash2,
  Loader2,
  Pencil,
  MoreVertical,
  Power,
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  useNotifications,
  useCreateNotification,
  useUpdateNotification,
  useDeleteNotification,
} from '@/hooks/use-notifications';
import type { NotificationType } from '@/types';
import { cn } from '@/lib/utils';

const NotificationsPage = () => {
  const [page, setPage] = useState(1);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingNotificationId, setEditingNotificationId] = useState<string | null>(null);
  const [newChannelType, setNewChannelType] = useState<NotificationType>('email');
  const [newChannelName, setNewChannelName] = useState('');
  const [newChannelConfig, setNewChannelConfig] = useState({
    email: '',
    webhook_url: '',
    channel: '',
  });

  // Fetch notifications
  const { data: notificationsData, isLoading: isLoadingNotifications } = useNotifications(page, 10);

  // Mutations
  const createNotification = useCreateNotification();
  const updateNotification = useUpdateNotification();
  const deleteNotification = useDeleteNotification();

  const notifications = notificationsData?.data || [];

  // Debug: Log when dialog state changes
  useEffect(() => {
    console.log('Dialog state changed to:', isDialogOpen);
  }, [isDialogOpen]);

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

  const resetForm = () => {
    setNewChannelName('');
    setNewChannelConfig({ email: '', webhook_url: '', channel: '' });
    setNewChannelType('email');
    setEditingNotificationId(null);
  };

  const handleEditChannel = (notification: (typeof notifications)[0]) => {
    setEditingNotificationId(notification.id);
    setNewChannelType(notification.type);
    setNewChannelName(notification.name);
    setNewChannelConfig({
      email: notification.config.email || '',
      webhook_url: notification.config.webhook_url || '',
      channel: notification.config.channel || '',
    });
    setIsDialogOpen(true);
  };

  const handleAddChannel = async () => {
    if (!newChannelName.trim()) {
      toast.error('Please enter a channel name');
      return;
    }

    // Validate config based on type
    if (newChannelType === 'email') {
      if (!newChannelConfig.email) {
        toast.error('Please enter an email address');
        return;
      }
    } else {
      if (!newChannelConfig.webhook_url) {
        toast.error('Please enter a webhook URL');
        return;
      }
    }

    try {
      const config =
        newChannelType === 'email'
          ? { email: newChannelConfig.email }
          : { webhook_url: newChannelConfig.webhook_url };

      if (editingNotificationId) {
        // Update existing notification
        await updateNotification.mutateAsync({
          notificationId: editingNotificationId,
          data: {
            name: newChannelName,
            config,
          },
        });
        toast.success('Notification channel updated successfully');
      } else {
        // Create new notification
        await createNotification.mutateAsync({
          type: newChannelType,
          name: newChannelName,
          enabled: true,
          config,
        });
        toast.success('Notification channel created successfully');
      }

      setIsDialogOpen(false);
      resetForm();
    } catch (error: any) {
      console.error(
        `Error ${editingNotificationId ? 'updating' : 'creating'} notification:`,
        error
      );
      const errorMessage =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        `Failed to ${editingNotificationId ? 'update' : 'create'} notification channel`;
      toast.error(errorMessage);
    }
  };

  const handleDeleteChannel = async (id: string) => {
    if (!confirm('Are you sure you want to delete this notification channel?')) {
      return;
    }

    try {
      await deleteNotification.mutateAsync(id);
      toast.success('Notification channel deleted successfully');
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Failed to delete notification channel');
    }
  };

  const handleToggleChannel = async (notification: (typeof notifications)[0]) => {
    try {
      await updateNotification.mutateAsync({
        notificationId: notification.id,
        data: {
          enabled: !notification.enabled,
        },
      });
      toast.success(
        `Notification channel ${!notification.enabled ? 'enabled' : 'disabled'} successfully`
      );
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Failed to update notification channel');
    }
  };

  // Empty state
  if (!isLoadingNotifications && notifications.length === 0 && page === 1) {
    return (
      <>
        <div className="min-h-screen bg-background p-8 pl-32">
          <div className="container mx-auto max-w-6xl">
            <FadeIn>
              <div className="mb-8 flex items-center justify-between relative z-10">
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">Notification Channels</h1>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Configure how you receive notifications about webhook executions
                  </p>
                </div>
                <Button
                  type="button"
                  onClick={() => {
                    console.log('Add Channel button clicked (empty state)');
                    setIsDialogOpen(true);
                  }}
                  className="cursor-pointer relative z-20"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Channel
                </Button>
              </div>

              {/* Empty State */}
              <div className="mt-16 flex flex-col items-center justify-center rounded-lg border border-dashed border-muted-foreground/25 bg-muted/5 p-16 text-center">
                <div className="rounded-full bg-muted/50 p-4">
                  <Bell className="h-10 w-10 text-muted-foreground/50" />
                </div>
                <h2 className="mt-6 text-xl font-semibold">No notification channels yet</h2>
                <p className="mt-2 max-w-md text-sm text-muted-foreground">
                  Get started by creating your first notification channel. Configure email, Slack,
                  Discord, or webhook notifications to stay informed about your webhook executions.
                </p>
                <Button
                  type="button"
                  onClick={() => {
                    console.log('Add Notification Channel button clicked');
                    setIsDialogOpen(true);
                  }}
                  className="mt-6 cursor-pointer"
                  size="lg"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Notification Channel
                </Button>
              </div>
            </FadeIn>
          </div>
        </div>

        {/* Add/Edit Notification Channel Dialog */}
        <Dialog
          open={isDialogOpen}
          onOpenChange={(open) => {
            setIsDialogOpen(open);
            if (!open) {
              resetForm();
            }
          }}
        >
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>
                {editingNotificationId ? 'Edit Notification Channel' : 'Add Notification Channel'}
              </DialogTitle>
              <DialogDescription>
                {editingNotificationId
                  ? 'Update the notification channel configuration'
                  : 'Configure a new channel to receive webhook execution notifications'}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Channel Type</Label>
                <Select
                  value={newChannelType}
                  onValueChange={(value: NotificationType) => setNewChannelType(value)}
                  disabled={!!editingNotificationId}
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
                  <Label>Email Address *</Label>
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
                  <Label>Webhook URL *</Label>
                  <Input
                    type="url"
                    placeholder="https://hooks.slack.com/services/..."
                    value={newChannelConfig.webhook_url}
                    onChange={(e) =>
                      setNewChannelConfig({
                        ...newChannelConfig,
                        webhook_url: e.target.value,
                      })
                    }
                  />
                </div>
              )}
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setIsDialogOpen(false);
                  resetForm();
                }}
                disabled={createNotification.isPending || updateNotification.isPending}
              >
                Cancel
              </Button>
              <Button
                onClick={handleAddChannel}
                disabled={createNotification.isPending || updateNotification.isPending}
              >
                {createNotification.isPending || updateNotification.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {editingNotificationId ? 'Updating...' : 'Creating...'}
                  </>
                ) : editingNotificationId ? (
                  'Update Channel'
                ) : (
                  'Add Channel'
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </>
    );
  }

  return (
    <>
      <div className="min-h-screen bg-background p-8 pl-32">
        <div className="container mx-auto max-w-6xl">
          <FadeIn>
            {/* Header */}
            <div className="mb-8 flex items-center justify-between relative z-10">
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Notification Channels</h1>
                <p className="mt-1 text-sm text-muted-foreground">
                  Configure how you receive notifications about webhook executions
                </p>
              </div>
              <Button
                type="button"
                onClick={() => {
                  console.log('Add Channel button clicked, opening dialog');
                  setIsDialogOpen(true);
                }}
                className="cursor-pointer relative z-20"
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Channel
              </Button>
            </div>

            {/* Loading State */}
            {isLoadingNotifications && (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <Card key={i} className="rounded-xl border-border/50">
                    <CardContent className="flex items-center justify-between p-4">
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <Skeleton className="h-10 w-10 rounded" />
                        <div className="flex-1 space-y-2 min-w-0">
                          <Skeleton className="h-4 w-48" />
                          <Skeleton className="h-3 w-64" />
                        </div>
                      </div>
                      <Skeleton className="h-6 w-11 rounded-full" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Notifications List */}
            {!isLoadingNotifications && notifications.length > 0 && (
              <div className="space-y-3">
                {notifications.map((channel) => {
                  const Icon = getChannelIcon(channel.type);
                  return (
                    <Card
                      key={channel.id}
                      className="group rounded-xl border-border/50 bg-card transition-all shadow-none duration-200 hover:border-border hover:shadow-sm"
                    >
                      <CardContent className="flex items-center justify-between gap-6 p-4">
                        {/* Left Side - Information */}
                        <div className="flex items-center gap-4 flex-1 min-w-0">
                          <div
                            className={cn(
                              'flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg',
                              channel.enabled ? 'bg-primary/10' : 'bg-muted/50'
                            )}
                          >
                            <Icon
                              className={cn(
                                'h-5 w-5',
                                channel.enabled ? 'text-primary' : 'text-muted-foreground'
                              )}
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-semibold text-sm text-foreground truncate">
                                {channel.name}
                              </h3>
                              <Badge variant="outline" className="text-xs">
                                {getChannelLabel(channel.type)}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                              {channel.type === 'email' && (
                                <div className="flex items-center gap-1.5 min-w-0">
                                  <Mail className="h-3 w-3 flex-shrink-0" />
                                  <span className="truncate">{channel.config.email}</span>
                                </div>
                              )}
                              {(channel.type === 'slack' ||
                                channel.type === 'discord' ||
                                channel.type === 'webhook') && (
                                <div className="flex items-center gap-1.5 min-w-0">
                                  <Webhook className="h-3 w-3 flex-shrink-0" />
                                  <code className="truncate font-mono text-xs max-w-[300px]">
                                    {channel.config.webhook_url || 'Not configured'}
                                  </code>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Right Side - Actions */}
                        <div
                          className="flex items-center gap-3 flex-shrink-0"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              channel.enabled
                                ? 'text-green-600 border-green-600'
                                : 'text-muted-foreground border-muted-foreground'
                            )}
                          >
                            {channel.enabled ? 'Enabled' : 'Disabled'}
                          </Badge>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0"
                                disabled={
                                  updateNotification.isPending || deleteNotification.isPending
                                }
                              >
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() => handleToggleChannel(channel)}
                                disabled={updateNotification.isPending}
                              >
                                <Power className="mr-2 h-4 w-4" />
                                {channel.enabled ? 'Disable' : 'Enable'}
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => handleEditChannel(channel)}
                                disabled={
                                  updateNotification.isPending || deleteNotification.isPending
                                }
                              >
                                <Pencil className="mr-2 h-4 w-4" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => handleDeleteChannel(channel.id)}
                                disabled={
                                  deleteNotification.isPending || updateNotification.isPending
                                }
                                className="text-destructive focus:text-destructive"
                              >
                                {deleteNotification.isPending ? (
                                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                  <Trash2 className="mr-2 h-4 w-4" />
                                )}
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </FadeIn>
        </div>
      </div>

      {/* Add/Edit Notification Channel Dialog */}
      <Dialog
        open={isDialogOpen}
        onOpenChange={(open) => {
          setIsDialogOpen(open);
          if (!open) {
            resetForm();
          }
        }}
      >
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {editingNotificationId ? 'Edit Notification Channel' : 'Add Notification Channel'}
            </DialogTitle>
            <DialogDescription>
              {editingNotificationId
                ? 'Update the notification channel configuration'
                : 'Configure a new channel to receive webhook execution notifications'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Channel Type</Label>
              <Select
                value={newChannelType}
                onValueChange={(value: NotificationType) => setNewChannelType(value)}
                disabled={!!editingNotificationId}
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
                <Label>Email Address *</Label>
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
                <Label>Webhook URL *</Label>
                <Input
                  type="url"
                  placeholder="https://hooks.slack.com/services/..."
                  value={newChannelConfig.webhook_url}
                  onChange={(e) =>
                    setNewChannelConfig({
                      ...newChannelConfig,
                      webhook_url: e.target.value,
                    })
                  }
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsDialogOpen(false);
                resetForm();
              }}
              disabled={createNotification.isPending || updateNotification.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddChannel}
              disabled={createNotification.isPending || updateNotification.isPending}
            >
              {createNotification.isPending || updateNotification.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {editingNotificationId ? 'Updating...' : 'Creating...'}
                </>
              ) : editingNotificationId ? (
                'Update Channel'
              ) : (
                'Add Channel'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default NotificationsPage;
