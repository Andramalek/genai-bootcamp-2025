import { Link, useLocation } from 'react-router-dom';
import { Home, Book, BookOpen, Group, History, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Study Activities', href: '/study-activities', icon: Book },
  { name: 'Words', href: '/words', icon: BookOpen },
  { name: 'Word Groups', href: '/groups', icon: Group },
  { name: 'Sessions', href: '/sessions', icon: History },
  { name: 'Settings', href: '/settings', icon: Settings },
];

function getBreadcrumbs(pathname: string) {
  const paths = pathname.split('/').filter(Boolean);
  return paths.map((path, index) => {
    const href = `/${paths.slice(0, index + 1).join('/')}`;
    const name = path.charAt(0).toUpperCase() + path.slice(1).replace(/-/g, ' ');
    return { name, href };
  });
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const breadcrumbs = getBreadcrumbs(location.pathname);

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="mr-8 hidden md:flex">
            <Link to="/" className="text-xl font-bold text-primary">
              Japanese Learning
            </Link>
          </div>
          <nav className="flex items-center space-x-2 text-sm font-medium">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  to={item.href}
                >
                  <Button
                    variant={isActive ? "destructive" : "outline"}
                    className="gap-2"
                  >
                    <Icon className="h-4 w-4" />
                    {item.name}
                  </Button>
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      <div className="container py-4">
        <nav className="flex" aria-label="Breadcrumb">
          <ol className="flex items-center space-x-2">
            {breadcrumbs.map((breadcrumb, index) => (
              <li key={breadcrumb.href} className="flex items-center">
                {index > 0 && <span className="mx-2 text-gray-400">/</span>}
                <Link
                  to={breadcrumb.href}
                  className={cn(
                    "text-sm font-medium",
                    index === breadcrumbs.length - 1
                      ? "text-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {breadcrumb.name}
                </Link>
              </li>
            ))}
          </ol>
        </nav>
        <Separator className="my-4" />
        <main>{children}</main>
      </div>
    </div>
  );
}