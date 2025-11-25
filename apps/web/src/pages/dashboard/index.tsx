import { useNavigate } from 'react-router-dom';
import { useCurrentUser } from '@/hooks/use-auth';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

const DashboardPage = () => {
  const navigate = useNavigate();

  // Fetch current user data
  useCurrentUser();

  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto max-w-4xl">
        <FadeIn>
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
            <h1 className="text-4xl font-bold tracking-tight mb-4">Welcome to Scheduler</h1>
            <p className="text-lg text-muted-foreground mb-8 max-w-2xl">
              Manage your scheduled webhooks and automate your workflows with ease.
            </p>
            <div className="flex gap-4">
              <Button onClick={() => navigate('/schedules')} size="lg">
                View Schedules
              </Button>
              <Button onClick={() => navigate('/add-new')} size="lg" variant="outline">
                <Plus className="mr-2 h-4 w-4" />
                Create Schedule
              </Button>
            </div>
          </div>
        </FadeIn>
      </div>
    </div>
  );
};

export default DashboardPage;
